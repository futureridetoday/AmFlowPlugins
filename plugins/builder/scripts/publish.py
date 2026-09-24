#!/usr/bin/env python3
"""`publish.py` — a parte determinística do envio de um recurso revisado ao Hub.

Scanner de segurança em camadas (plano publish-reviewed-only, decisão 6): camada 1, só um recurso
com `amflow-status: reviewed` chega ao bundle; camada 2 (plano require-secure-invite), o
secure-invite check — presente, identidade e file digests batendo com o disco, sem rede (index.md
§6). Monta o pacote com `montar_bundle` (`review.py`) — a mesma seleção que a revisão mede —
mapeado para o caminho canônico que o Hub aceita (`.claude/<tipo>s/<nome>/…`, medido em
`teste-publish-hub-producao.md`), e grava o resultado da submissão só depois do aceite, pelo
escritor de `status.py`.

Este script é chamado mais de uma vez, por donos diferentes (index.md §6): o comando `publish.md`
roda `--conferir` logo depois da escolha do recurso (decisão 28), antes de preço, changelog e
confirmação M10 — barra cedo o que não vai publicar; o agent `resource-publisher` roda sem flag,
para reconferir as camadas 1 e 2 e montar o bundle no envio, e de novo depois da resposta do Hub,
só quando ela foi aceita, com `--registrar`, para registrar. As condições que dependem de rede —
submissão pendente, versão e dependências em produção — são do agent, que já tem as tools MCP; este
script nunca chama rede, mesmo padrão do `review.py` (cuja única chamada de rede, a `me`, também
fica no agent).

Cross-repo: nasce aqui e desce a `plugins/builder/scripts/publish.py` do AmFlowPlugins pelo
`vendor.py` — mesmo mecanismo do `check.py`, do `status.py` e do `review.py`.

Uso:
  publish.py <projeto> <local>
  publish.py <projeto> <local> --conferir
  publish.py <projeto> <local> --versao-producao <versao>
  publish.py <projeto> <local> --registrar --hub-id <uuid> --versao <versao>

`<local>` é o caminho do manifesto relativo ao projeto — o mesmo que `status.py list` imprime na
coluna Local. A revisão cobre só `skill` e `agent` (`identificar`, reusado de `review.py`); os
outros tipos nunca chegam a `reviewed`, então nunca passam da camada 1.

`--conferir` roda as camadas 1 e 2 sobre o recurso, sem montar o pacote — decisão 28: o
`publish.md` chama logo depois da escolha (Fase 2), antes de preço, changelog e confirmação M10,
para barrar cedo o que não vai publicar.

`--versao-producao` compara a versão local com a versão em produção (decisão 7 do plano: sem
bump automático — igual ou menor é barrada). O valor de produção vem do `get_resource`, chamada
de rede que só o comando ou o agent fazem; a comparação em si não precisa de rede, e por isso
mora aqui, testável, em vez de deixada como prosa para quem executa o comando interpretar.

Sai com 0 quando o resultado é `OK` (ou, com `--registrar`, quando a gravação foi aceita; com
`--conferir` ou `--versao-producao`, quando a conferência/a local supera); 1 quando alguma camada
barra o envio, ou a versão local não supera a produção; 2 se a chamada não é válida.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _carregar_review():
    """Carrega `review.py`, irmão deste arquivo — reusa `identificar`, `montar_bundle` e `_versao`."""
    caminho = Path(__file__).resolve().parent / "review.py"
    if not caminho.is_file():
        raise RuntimeError("review.py não encontrado ao lado de publish.py")
    spec = importlib.util.spec_from_file_location("builder_review", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _carregar_status():
    """Carrega `status.py`, irmão deste arquivo — reusa `varrer` e o escritor `registrar_publicado`."""
    caminho = Path(__file__).resolve().parent / "status.py"
    if not caminho.is_file():
        raise RuntimeError("status.py não encontrado ao lado de publish.py")
    spec = importlib.util.spec_from_file_location("builder_status", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


review = _carregar_review()
status = _carregar_status()
check = review.check  # já carregado por review.py — mesma instância, nunca uma segunda cópia


class ErroUso(Exception):
    """Chamada inválida — o script não chega a preparar nada. Sai com 2, mensagem em stderr."""


@dataclass
class Preparo:
    ok: bool
    tipo: str = ""
    nome: str = ""
    versao: str | None = None
    hub_id: str | None = None
    arquivos: dict[str, str] = field(default_factory=dict)  # caminho canônico → conteúdo
    omitidos: dict[str, str] = field(default_factory=dict)  # caminho relativo → motivo
    secure_invite: str | None = None  # JWS de uma linha, lido de disco sem transformação
    motivo: str | None = None


def _hub_id(fm, tipo: str) -> str | None:
    """Onde o identificador do Hub mora hoje, por tipo — mesmas constantes que `status._gravar_hub_id`
    usa para gravar, nunca uma segunda cópia dos literais."""
    campo = fm.metadata.get(status.CHAVE_HUB_ID_SKILL) if tipo == "skill" else fm.topo.get(status.CHAVE_HUB_ID_TOPO)
    return campo.texto if campo and campo.texto else None


# Mensagens do secure-invite check (camada 2, index.md §6) — texto congelado, citado literalmente.
_MSG_SECURE_INVITE_AUSENTE = (
    "Este recurso não tem secure-invite. Rode `/amflow-builder:review` para revisar e obter um "
    "secure-invite antes de publicar."
)
_MSG_IDENTIDADE_DIFERENTE = (
    "O tipo, o nome ou a versão do recurso mudaram desde a revisão. Rode `/amflow-builder:review` "
    "novamente antes de publicar."
)


def _verificar_secure_invite(alvo, tipo: str, nome: str, versao: str | None) -> tuple[str | None, str | None]:
    """Secure-invite check — camada 2 do scanner (index.md §6), sem rede. `(None, texto)` quando
    bate: secure-invite presente, identidade do payload igual à do manifesto em disco, e os file
    digests do payload iguais aos recalculados agora. `(motivo, None)` na primeira recusa."""
    arquivo = alvo.pasta / review.NOME_SECURE_INVITE
    if not arquivo.is_file():
        return _MSG_SECURE_INVITE_AUSENTE, None
    texto = arquivo.read_text(encoding="utf-8")
    try:
        payload = review.decodificar_secure_invite(texto)
    except ValueError:
        return _MSG_SECURE_INVITE_AUSENTE, None

    recurso_payload = payload.get("resource") or {}
    if (
        recurso_payload.get("type") != tipo
        or recurso_payload.get("name") != nome
        or recurso_payload.get("version") != versao
    ):
        return _MSG_IDENTIDADE_DIFERENTE, None

    bundle = review.montar_bundle(alvo.pasta)
    digests_atuais = {
        review._caminho_canonico(alvo, rel): hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
        for rel, conteudo in bundle.selecionados.items()
    }
    digests_payload = payload.get("file_digests") or {}
    for caminho in sorted(set(digests_atuais) | set(digests_payload)):
        if digests_atuais.get(caminho) != digests_payload.get(caminho):
            return (
                f"O arquivo `{caminho}` foi editado depois da revisão. Rode `/amflow-builder:review` "
                "novamente antes de publicar."
            ), None
    return None, texto


def _checar_camadas(projeto: Path, local: str):
    """Camadas 1 e 2 (index.md §6). Devolve `(alvo, fm, versao, secure_invite, motivo)` — `motivo`
    é `None` só quando as duas camadas passam; os demais campos ficam `None` quando a recusa
    acontece antes de o frontmatter ser lido."""
    try:
        alvo = review.identificar(projeto, local)
    except review.ErroUso as exc:
        raise ErroUso(str(exc))

    todos, _ = status.varrer(projeto)
    recurso = next((r for r in todos if r.caminho.resolve() == alvo.manifesto.resolve()), None)
    if recurso is None:
        return alvo, None, None, None, f"recurso não encontrado — {alvo.manifesto}"
    if recurso.status != "reviewed":
        return alvo, None, None, None, (
            f"camada 1: só publica recurso 'reviewed' — {alvo.tipo}/{alvo.nome} está em "
            f"'{recurso.status or 'sem status'}'"
        )

    texto = alvo.manifesto.read_text(encoding="utf-8")
    fm = check.parsear(texto)
    if fm is None:
        return alvo, None, None, None, f"frontmatter ausente ou malformado — {alvo.manifesto}"

    versao = review._versao(fm, alvo.tipo)
    motivo, secure_invite = _verificar_secure_invite(alvo, alvo.tipo, alvo.nome, versao)
    if motivo:
        return alvo, fm, versao, None, motivo
    return alvo, fm, versao, secure_invite, None


def conferir(projeto: Path, local: str) -> tuple[bool, str | None]:
    """Camadas 1 e 2, sem montar o pacote (decisão 28) — `publish.md` chama logo depois da escolha
    do recurso, antes de preço, changelog e confirmação M10."""
    _, _, _, _, motivo = _checar_camadas(projeto, local)
    return motivo is None, motivo


def preparar(projeto: Path, local: str) -> Preparo:
    """Camadas 1 e 2 e seleção do bundle. Refeito sempre que chamado, mesmo fora da listagem do
    comando: quem chama este script direto sobre um recurso fora de `reviewed`, ou sem
    secure-invite válido, não passa daqui — é a barreira que vale independente de quem chamou
    (mesmo desenho do `--registrar` do `review.py` para o `reviewed`)."""
    alvo, fm, versao, secure_invite, motivo = _checar_camadas(projeto, local)
    if motivo:
        return Preparo(False, motivo=motivo)

    bundle = review.montar_bundle(alvo.pasta)
    arquivos = {review._caminho_canonico(alvo, rel): conteudo for rel, conteudo in bundle.selecionados.items()}
    return Preparo(
        True,
        tipo=alvo.tipo,
        nome=alvo.nome,
        versao=versao,
        hub_id=_hub_id(fm, alvo.tipo),
        arquivos=arquivos,
        omitidos=bundle.omitidos,
        secure_invite=secure_invite,
    )


_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _versao_tupla(v: str) -> tuple[int, int, int] | None:
    """`(major, minor, patch)` de uma versão semver `X.Y.Z` — `None` se não bater o formato."""
    m = _SEMVER_RE.fullmatch(v.strip())
    if not m:
        return None
    return tuple(int(g) for g in m.groups())


def versao_supera(local: str, producao: str) -> bool | None:
    """`True` se `local` > `producao`, numericamente (semver) — nunca comparação léxica de
    string, onde "1.10.0" perderia para "1.9.0". `None` quando algum dos dois não é `X.Y.Z`, e
    quem chama decide o fallback: o Hub sempre teve a palavra final sobre a versão."""
    t_local, t_producao = _versao_tupla(local), _versao_tupla(producao)
    if t_local is None or t_producao is None:
        return None
    return t_local > t_producao


def checar_versao(projeto: Path, local: str, producao: str) -> tuple[bool, str]:
    """Decisão 7 do plano: sem bump automático — atualização com versão igual ou menor que a de
    produção é barrada antes do envio. `producao` é o valor que o `get_resource` devolveu (rede,
    fora deste script); a comparação em si é pura e determinística, então mora em código, com
    teste, em vez de prosa interpretada por quem executa o comando."""
    try:
        alvo = review.identificar(projeto, local)
    except review.ErroUso as exc:
        raise ErroUso(str(exc))
    texto = alvo.manifesto.read_text(encoding="utf-8")
    fm = check.parsear(texto)
    if fm is None:
        raise ErroUso(f"frontmatter ausente ou malformado — {alvo.manifesto}")
    versao_local = review._versao(fm, alvo.tipo)
    if not versao_local:
        raise ErroUso(f"versão ausente no manifesto — {alvo.manifesto}")

    supera = versao_supera(versao_local, producao)
    if supera is False:
        return False, (
            f"Versão local ({versao_local}) não supera a versão em produção ({producao}). Suba a "
            "versão no frontmatter e rode /amflow-builder:review de novo — a publicação envia "
            "exatamente o que foi revisado, sem bump automático."
        )
    if supera is None:
        return True, (
            f"Versão local ({versao_local}) ou produção ({producao}) fora do formato semver "
            "X.Y.Z — seguindo; quem decide é o Hub."
        )
    return True, f"Versão local ({versao_local}) supera a produção ({producao})."


def registrar(projeto: Path, local: str, hub_id: str, versao: str):
    """Grava depois do aceite do Hub, com o escritor do `status.py`. Devolve o `ResultadoSet` dele."""
    alvo = review.identificar(projeto, local)
    return status.registrar_publicado(projeto, alvo.manifesto, hub_id, versao)


def formatar(preparo: Preparo) -> str:
    if not preparo.ok:
        return f"RESULTADO: BARRADO\nMOTIVO: {preparo.motivo}"
    saida = [
        "RESULTADO: OK",
        f"RECURSO: {preparo.tipo}/{preparo.nome}" + (f" v{preparo.versao}" if preparo.versao else ""),
        f"HUB_ID: {preparo.hub_id or ''}",
        f"SECURE_INVITE: {preparo.secure_invite or ''}",
    ]
    if preparo.omitidos:
        saida.append("OMITIDOS:")
        saida += [f"  {caminho}: {motivo}" for caminho, motivo in preparo.omitidos.items()]
    saida.append("ARQUIVOS_JSON:")
    saida.append(json.dumps(preparo.arquivos, ensure_ascii=False))
    return "\n".join(saida)


# ── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("projeto", type=Path)
    parser.add_argument("local", help="caminho do manifesto relativo ao projeto — ex.: skills/deep-research/SKILL.md")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--registrar", action="store_true", help="grava depois do aceite do Hub — exige --hub-id e --versao")
    grupo.add_argument(
        "--conferir",
        action="store_true",
        help="confere as camadas 1 e 2, sem montar o pacote — decisão 28",
    )
    grupo.add_argument(
        "--versao-producao",
        default=None,
        metavar="VERSAO",
        help="compara a versão local com a versão em produção — decisão 7 do plano",
    )
    parser.add_argument("--hub-id", default=None, help="uuid devolvido pelo Hub — exigido com --registrar")
    parser.add_argument("--versao", default=None, help="versão submetida — exigida com --registrar")
    args = parser.parse_args(argv)

    projeto = args.projeto.expanduser().resolve()
    if not projeto.is_dir():
        print(f"erro: projeto não encontrado — {projeto}", file=sys.stderr)
        return 2

    if args.conferir:
        try:
            ok, motivo = conferir(projeto, args.local)
        except ErroUso as exc:
            print(f"erro: {exc}", file=sys.stderr)
            return 2
        print(f"RESULTADO: {'OK' if ok else 'BARRADO'}")
        if motivo:
            print(f"MOTIVO: {motivo}")
        return 0 if ok else 1

    if args.versao_producao is not None:
        try:
            ok, mensagem = checar_versao(projeto, args.local, args.versao_producao)
        except ErroUso as exc:
            print(f"erro: {exc}", file=sys.stderr)
            return 2
        print(f"RESULTADO: {'OK' if ok else 'INSUFICIENTE'}")
        print(f"MOTIVO: {mensagem}")
        return 0 if ok else 1

    if args.registrar:
        if not args.hub_id:
            print("erro: --registrar exige --hub-id", file=sys.stderr)
            return 2
        if not args.versao:
            print("erro: --registrar exige --versao", file=sys.stderr)
            return 2
        try:
            resultado = registrar(projeto, args.local, args.hub_id, args.versao)
        except (ErroUso, review.ErroUso) as exc:
            print(f"erro: {exc}", file=sys.stderr)
            return 2
        print(resultado.mensagem)
        return 0 if resultado.ok else 2

    try:
        preparo = preparar(projeto, args.local)
    except ErroUso as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    print(formatar(preparo))
    return 0 if preparo.ok else 1


if __name__ == "__main__":
    sys.exit(main())

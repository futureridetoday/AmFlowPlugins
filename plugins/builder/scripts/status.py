#!/usr/bin/env python3
"""`status.py` — todo o determinismo do status dos recursos do Creator.

Varre os cinco tipos de recurso (`skill`, `agent`, `command`, `hook`, `module`) de um projeto
de Creator, lê e grava `metadata.amflow-status`, valida o domínio, filtra, ordena pela próxima
ação e recusa o que não é decisão do Creator. A skill `/amflow-builder:status`
(`docs/plan/builder/0014-unify-status-field/06-status-skill.md`) só interpreta o pedido e chama
este script — nenhum determinismo mora em prosa (princípio *Determinismo em código*).

Domínio, rótulos, localização por tipo, chave do motivo, ordem da saída e precedência sobre o
lugar legado vêm de `docs/plan/builder/0014-unify-status-field/index.md` — este arquivo não os
redeclara em prosa, só em código. O conjunto de valores válidos (`STATUS_VALIDOS`/`STATUS_LEGADO`)
é reusado de `check.py` (unidade 0014-02): uma definição só evita as duas se divergirem.

Cross-repo: nasce aqui, em `scripts/`, e desce a `plugins/builder/scripts/status.py` do
AmFlowPlugins por `vendor.py` — mesmo mecanismo do `check.py`. A cópia é gerada, nunca editada do
outro lado. Por isso este arquivo localiza `check.py` em dois lugares possíveis: como irmão, no
mesmo diretório (é onde ele está depois do `vendor.py`, em `plugins/builder/scripts/`), ou em
`frontmatter/`, um nível abaixo (é onde ele está na fonte, em `scripts/frontmatter/`).

Uso:
  status.py list <projeto> [--status <valor>]
  status.py set <projeto> <recurso> <valor> [--motivo <texto>]

`<recurso>` é `<tipo>/<nome>` — ex.: `skill/deep-research`, `agent/reviewer`.

Sai com 0 em sucesso; 1 se `list` encontrou arquivo que não parseia, ou se `set` foi recusado.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ── check.py — reusado, nunca redeclarado (dependência 0014-02) ───────────────


def _carregar_check():
    """Carrega `check.py` de onde ele estiver — irmão (plugin, pós-vendor) ou `frontmatter/` (fonte).

    `importlib` por caminho, não `sys.path.insert` + `import check`: evita que este processo
    sombreie um `check` de outro lugar do `sys.path`. O registro em `sys.modules` antes do
    `exec_module` é necessário porque `check.py` usa `from __future__ import annotations` com
    `@dataclass` — mesma necessidade já documentada em `scripts/frontmatter/tests/test_check.py`.
    """
    base = Path(__file__).resolve().parent
    for candidato in (base / "check.py", base / "frontmatter" / "check.py"):
        if candidato.is_file():
            spec = importlib.util.spec_from_file_location("frontmatter_check", candidato)
            modulo = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = modulo
            spec.loader.exec_module(modulo)
            return modulo
    raise RuntimeError("check.py não encontrado — nem como irmão, nem em frontmatter/")


check = _carregar_check()

STATUS_VALIDOS = check.STATUS_VALIDOS
STATUS_LEGADO = check.STATUS_LEGADO
DOMINIO = STATUS_VALIDOS | STATUS_LEGADO

# ── domínio próprio desta unidade — index.md §1, §3, §4; check.py não o declara ───

CHAVE_STATUS = "amflow-status"
CHAVE_MOTIVO = "amflow-status-reason"

# index.md §1 — "Gravados pela publicação a partir do Hub". Só os dois comandos de
# publicação gravam estes quatro; `set` sempre os recusa (Contrato, linha Erro).
VALORES_HUB = frozenset({"pending_review", "changes_requested", "rejected", "published"})

# index.md §1 — "Declarados pelo Creator". É o único subconjunto que `set` aceita gravar.
VALORES_CREATOR = STATUS_VALIDOS - VALORES_HUB

# index.md §1, coluna Rótulo.
ROTULOS = {
    "in_progress": "Em andamento",
    "paused": "Pausado",
    "blocked": "Bloqueado",
    "review": "Pronto para publicar",
    "deprecated": "Descontinuado",
    "pending_review": "Em revisão",
    "changes_requested": "Ajustes pedidos",
    "rejected": "Recusado",
    "published": "Publicado",
}

# index.md §4 — ordem congelada, primeiro o que precisa de ação do Creator.
ORDEM_SAIDA = (
    "changes_requested",
    "rejected",
    "review",
    "in_progress",
    "blocked",
    "pending_review",
    "paused",
    "published",
    "deprecated",
)

TIPOS = ("skill", "agent", "command", "hook", "module")


@dataclass
class Recurso:
    tipo: str
    nome: str
    local: str  # caminho relativo a <projeto> — o que list exibe e set recebe como tipo/nome
    caminho: Path  # arquivo que carrega o campo, para leitura e escrita
    formato: str  # "yaml" | "json"
    lugar: str  # "dev" | "claude"
    status: str | None  # valor efetivo — metadata.amflow-status se presente, senão o legado
    lugar_legado: bool  # o campo antigo (status no topo/raiz) está presente no arquivo
    motivo: str | None = None


@dataclass
class ArquivoInvalido:
    tipo: str
    local: str
    erro: str


@dataclass
class ResultadoListagem:
    linhas: list[str]
    invalidos: list[ArquivoInvalido]
    total: int
    rodape: list[str]


@dataclass
class ResultadoSet:
    ok: bool
    mensagem: str


# ── leitura — parsear (check.py) para YAML, json da stdlib para JSON ──────────


def _resolver_status(novo: str | None, legado: str | None) -> tuple[str | None, bool]:
    """`metadata.amflow-status` vence (index.md §5); legado presente só marca a flag."""
    if novo:
        return novo, legado is not None
    if legado:
        return legado, True
    return None, False


def _ler_frontmatter(caminho: Path):
    """`(Frontmatter, None)` ou `(None, motivo do erro)` — nunca lança."""
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        return None, str(exc)
    fm = check.parsear(texto)
    if fm is None:
        return None, "frontmatter ausente ou malformado — sem '---' de abertura e fechamento"
    return fm, None


def _ler_json(caminho: Path):
    """`(dict, None)` ou `(None, motivo do erro)` — nunca lança."""
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        return None, str(exc)
    try:
        return json.loads(texto), None
    except json.JSONDecodeError as exc:
        return None, f"JSON inválido: {exc}"


def _recurso_yaml(
    tipo: str, nome: str, caminho: Path, projeto: Path, chave_legado: str | None
) -> tuple[Recurso | None, ArquivoInvalido | None]:
    """`(Recurso, None)`, `(None, ArquivoInvalido)`, ou `(None, None)` quando filtrado do escopo."""
    local = str(caminho.relative_to(projeto))
    fm, erro = _ler_frontmatter(caminho)
    if erro:
        return None, ArquivoInvalido(tipo, local, erro)
    if tipo == "skill" and "amflow-source" in fm.metadata:
        return None, None  # cópia instalada de skill de outro Creator — fora do alcance da norma
    campo_novo = fm.metadata.get(CHAVE_STATUS)
    campo_legado = fm.topo.get(chave_legado) if chave_legado else None
    campo_motivo = fm.metadata.get(CHAVE_MOTIVO)
    status, lugar_legado = _resolver_status(
        campo_novo.texto if campo_novo else None,
        campo_legado.texto if campo_legado else None,
    )
    motivo = campo_motivo.texto if campo_motivo else None
    return Recurso(tipo, nome, local, caminho, "yaml", _lugar(local), status, lugar_legado, motivo), None


def _recurso_json(
    tipo: str, nome: str, caminho: Path, projeto: Path, tem_legado: bool
) -> tuple[Recurso | None, ArquivoInvalido | None]:
    """`(Recurso, None)` ou `(None, ArquivoInvalido)`."""
    local = str(caminho.relative_to(projeto))
    dados, erro = _ler_json(caminho)
    if erro:
        return None, ArquivoInvalido(tipo, local, erro)
    metadata = dados.get("metadata") or {}
    status, lugar_legado = _resolver_status(
        metadata.get(CHAVE_STATUS),
        dados.get("status") if tem_legado else None,
    )
    motivo = metadata.get(CHAVE_MOTIVO)
    return Recurso(tipo, nome, local, caminho, "json", _lugar(local), status, lugar_legado, motivo), None


def _lugar(local: str) -> str:
    return "claude" if local.startswith(".claude/") else "dev"


def _nome_agente(caminho: Path) -> str:
    """Layout de pasta (`agents/<nome>/<nome>.md`) ou arquivo solto (`agents/<nome>.md`)."""
    return caminho.stem if caminho.parent.name == "agents" else caminho.parent.name


# ── varredura ──────────────────────────────────────────────────────────────
#
# Cada tipo usa um glob fixo, ancorado na raiz — nunca uma varredura recursiva. É isso que
# mantém `modules/*/module.json` fora de `skills/<nome>/modules/<outro>/module.json` (a cópia
# de módulo dentro de skill, index.md §"Placement de Recursos") sem precisar de exclusão à
# parte: o glob de `module` nunca desce dentro de `skills/`.
#
# Os padrões de `skill`, `agent` (dois layouts), `hook` e `command` seguem o que a unidade
# 0014-04 (verified) já mede em produção — `publish-status.md` Fase 1 — para as duas raízes
# (pasta de desenvolvimento e `.claude/`, decisão 4 do plano, enquanto a promoção existir).
# `module` não está lá (módulo não tem estado no Hub, decisão 6 do plano) mas entra aqui.


def varrer(projeto: Path) -> tuple[list[Recurso], list[ArquivoInvalido]]:
    recursos: list[Recurso] = []
    invalidos: list[ArquivoInvalido] = []

    for raiz in (projeto, projeto / ".claude"):
        for caminho in sorted(raiz.glob("skills/*/SKILL.md")):
            recurso, invalido = _recurso_yaml("skill", caminho.parent.name, caminho, projeto, None)
            _acumular(recursos, invalidos, recurso, invalido)

        candidatos_agent = sorted(raiz.glob("agents/*/*.md")) + sorted(raiz.glob("agents/*.md"))
        for caminho in candidatos_agent:
            if caminho.name.endswith("-description.md") or caminho.name.endswith("-workflow.md"):
                continue
            recurso, invalido = _recurso_yaml("agent", _nome_agente(caminho), caminho, projeto, "status")
            _acumular(recursos, invalidos, recurso, invalido)

        for caminho in sorted(raiz.glob("commands/*.md")):
            recurso, invalido = _recurso_yaml("command", caminho.stem, caminho, projeto, "status")
            _acumular(recursos, invalidos, recurso, invalido)

        for caminho in sorted(raiz.glob("hooks/*/hook.json")):
            recurso, invalido = _recurso_json("hook", caminho.parent.name, caminho, projeto, True)
            _acumular(recursos, invalidos, recurso, invalido)

        for caminho in sorted(raiz.glob("modules/*/module.json")):
            recurso, invalido = _recurso_json("module", caminho.parent.name, caminho, projeto, False)
            _acumular(recursos, invalidos, recurso, invalido)

    return recursos, invalidos


def _acumular(
    recursos: list[Recurso],
    invalidos: list[ArquivoInvalido],
    recurso: Recurso | None,
    invalido: ArquivoInvalido | None,
) -> None:
    if invalido is not None:
        invalidos.append(invalido)
    elif recurso is not None:
        recursos.append(recurso)


# ── list ───────────────────────────────────────────────────────────────────


def _formatar_linha(recurso: Recurso) -> str:
    anotacoes = []
    if recurso.status in VALORES_HUB:
        anotacoes.append("Hub")
    if recurso.lugar_legado:
        anotacoes.append("legado")
    if recurso.status is not None and recurso.status not in DOMINIO:
        anotacoes.append("fora do domínio")
    status_txt = recurso.status or "(sem status)"
    if anotacoes:
        status_txt = f"{status_txt} [{', '.join(anotacoes)}]"
    rotulo = ROTULOS.get(recurso.status, "—")
    return f"{recurso.tipo} | {recurso.nome} | {recurso.local} | {status_txt} | {rotulo}"


def _rodape(recursos: list[Recurso]) -> list[str]:
    """L-03 do plano — resolvida sem campo novo de data: a linha é a resposta a "de quando"."""
    linhas = []
    if any(r.status in VALORES_HUB for r in recursos):
        linhas.append(
            "[Hub] reflete a última execução do /amflow-builder:publish-status — rode-o de novo para atualizar."
        )
    if any(r.status == "pending_review" for r in recursos):
        linhas.append("Há recurso em revisão: rode /amflow-builder:publish-status para conferir.")
    return linhas


def _chave_ordem(recurso: Recurso) -> tuple[int, str, str]:
    try:
        posicao = ORDEM_SAIDA.index(recurso.status)
    except ValueError:
        posicao = len(ORDEM_SAIDA)
    return (posicao, recurso.tipo, recurso.nome)


def listar(projeto: Path, filtro_status: str | None = None) -> ResultadoListagem:
    todos, invalidos = varrer(projeto)
    visiveis = [r for r in todos if filtro_status is None or r.status == filtro_status]
    visiveis.sort(key=_chave_ordem)
    return ResultadoListagem(
        linhas=[_formatar_linha(r) for r in visiveis],
        invalidos=invalidos,
        total=len(visiveis),
        rodape=_rodape(todos),
    )


# ── set — escritor novo desta unidade (L-10 do plano; check.py só lê) ─────────

_RECURSO_RE = re.compile(r"^(skill|agent|command|hook|module)/(.+)$")
_CHAVE_LINHA_RE = re.compile(r"^([ \t]*[A-Za-z][A-Za-z0-9_.-]*:\s*)")


def _valor_yaml(valor: str) -> str:
    escapado = valor.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escapado}"'


def _substituir_valor(linha: str, novo_valor: str) -> str:
    """Troca só o valor da linha, preservando indentação e chave. Descarta comentário à direita
    — nenhuma das duas chaves que este escritor grava carrega comentário nos arquivos reais."""
    quebra = "\n" if linha.endswith("\n") else ""
    m = _CHAVE_LINHA_RE.match(linha)
    prefixo = m.group(1) if m else linha[: -len(quebra)] if quebra else linha
    return f"{prefixo}{novo_valor}{quebra}"


def _linha_fechamento_frontmatter(linhas: list[str]) -> int:
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            return i
    raise OSError("frontmatter sem '---' de fechamento")


def _escrever_yaml(recurso: Recurso, valor: str, motivo: str | None) -> None:
    texto = recurso.caminho.read_text(encoding="utf-8")
    fm = check.parsear(texto)
    if fm is None:
        raise OSError("frontmatter ausente ou malformado")
    linhas = texto.splitlines(keepends=True)

    campo_metadata = fm.topo.get("metadata")
    campo_status = fm.metadata.get(CHAVE_STATUS)
    campo_motivo = fm.metadata.get(CHAVE_MOTIVO)

    novas: list[str] = []

    if campo_status is not None:
        linhas[campo_status.linha - 1] = _substituir_valor(linhas[campo_status.linha - 1], valor)
    else:
        novas.append(f"  {CHAVE_STATUS}: {valor}\n")

    if motivo is not None:
        if campo_motivo is not None:
            linhas[campo_motivo.linha - 1] = _substituir_valor(linhas[campo_motivo.linha - 1], _valor_yaml(motivo))
        else:
            novas.append(f"  {CHAVE_MOTIVO}: {_valor_yaml(motivo)}\n")

    if campo_metadata is None:
        ponto = _linha_fechamento_frontmatter(linhas)
        linhas[ponto:ponto] = ["metadata:\n"] + novas
    elif novas:
        posicoes = [c.linha for c in fm.metadata.values()]
        ponto = max(posicoes) if posicoes else campo_metadata.linha
        linhas[ponto:ponto] = novas

    recurso.caminho.write_text("".join(linhas), encoding="utf-8")


def _escrever_json(recurso: Recurso, valor: str, motivo: str | None) -> None:
    """Round-trip json.loads/dumps. Preserva byte a byte quando a origem já segue `indent=2`,
    `ensure_ascii=False` — o estilo medido nos templates reais (hook.json, module.json)."""
    texto = recurso.caminho.read_text(encoding="utf-8")
    dados = json.loads(texto)
    metadata = dados.get("metadata")
    if metadata is None:
        metadata = {}
        dados["metadata"] = metadata
    metadata[CHAVE_STATUS] = valor
    if motivo is not None:
        metadata[CHAVE_MOTIVO] = motivo
    quebra_final = "\n" if texto.endswith("\n") else ""
    novo_texto = json.dumps(dados, indent=2, ensure_ascii=False) + quebra_final
    recurso.caminho.write_text(novo_texto, encoding="utf-8")


def atualizar(projeto: Path, recurso_id: str, valor: str, motivo: str | None = None) -> ResultadoSet:
    m = _RECURSO_RE.match(recurso_id)
    if not m:
        return ResultadoSet(
            False, f"recusado: identificador inválido '{recurso_id}' — use tipo/nome, ex.: skill/deep-research"
        )
    tipo, nome = m.groups()

    if valor in VALORES_HUB:
        return ResultadoSet(
            False, f"recusado: '{valor}' é gravado pela publicação (Hub) — não por esta ferramenta"
        )
    if valor not in VALORES_CREATOR:
        return ResultadoSet(
            False, f"recusado: '{valor}' fora do domínio — use um de {', '.join(sorted(VALORES_CREATOR))}"
        )
    if valor == "blocked" and not motivo:
        return ResultadoSet(False, "recusado: 'blocked' exige --motivo")

    todos, invalidos = varrer(projeto)
    candidatos = [r for r in todos if r.tipo == tipo and r.nome == nome]
    if not candidatos:
        for inv in invalidos:
            if inv.tipo == tipo and Path(inv.local).parent.name == nome:
                return ResultadoSet(False, f"recusado: {inv.local} não pôde ser interpretado — {inv.erro}")
        return ResultadoSet(False, f"recusado: recurso não encontrado — {recurso_id}")

    alvo = next((r for r in candidatos if r.lugar == "dev"), candidatos[0])
    status_antigo = alvo.status or "(sem status)"

    try:
        if alvo.formato == "yaml":
            _escrever_yaml(alvo, valor, motivo)
        else:
            _escrever_json(alvo, valor, motivo)
    except OSError as exc:
        return ResultadoSet(False, f"recusado: não foi possível gravar {alvo.local} — {exc}")

    return ResultadoSet(True, f"{tipo}/{nome}: {status_antigo} → {valor} ({alvo.local})")


# ── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p_list = sub.add_parser("list", help="lista os recursos do projeto e seus status")
    p_list.add_argument("projeto", type=Path)
    p_list.add_argument("--status", default=None)

    p_set = sub.add_parser("set", help="atualiza o status de um recurso")
    p_set.add_argument("projeto", type=Path)
    p_set.add_argument("recurso", help="tipo/nome — ex.: skill/deep-research")
    p_set.add_argument("valor")
    p_set.add_argument("--motivo", default=None)

    args = parser.parse_args(argv)
    projeto = args.projeto.expanduser().resolve()
    if not projeto.is_dir():
        print(f"erro: projeto não encontrado — {projeto}", file=sys.stderr)
        return 1

    if args.comando == "list":
        resultado = listar(projeto, args.status)
        for inv in resultado.invalidos:
            print(f"ERRO {inv.tipo} {inv.local}: {inv.erro}")
        for linha in resultado.linhas:
            print(linha)
        print()
        sufixo = f" (status={args.status})" if args.status else ""
        print(f"{resultado.total} recurso(s) encontrado(s){sufixo}")
        for linha in resultado.rodape:
            print(linha)
        return 1 if resultado.invalidos else 0

    resultado = atualizar(projeto, args.recurso, args.valor, args.motivo)
    print(resultado.mensagem)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    sys.exit(main())

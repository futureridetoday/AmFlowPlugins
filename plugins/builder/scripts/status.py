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
  status.py list <projeto> [--status <valor> ...]
  status.py set <projeto> <recurso> <valor> [--motivo <texto>]

`--status` é repetível; um valor terminado em `*` filtra por prefixo — `--status 'blocked-RG*'`
pega a família inteira (add-blocked-gate-id), sem pegar o `blocked` simples.

`<recurso>` é `<tipo>/<nome>` — ex.: `skill/deep-research`, `agent/resource-reviewer`.

Sai com 0 em sucesso; 1 se `list` encontrou arquivo que não parseia, ou se `set` foi recusado.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
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
BLOQUEIO_REVISAO_RE = check.BLOQUEIO_REVISAO_RE

# ── domínio próprio desta unidade — index.md §1, §3, §4; check.py não o declara ───

CHAVE_STATUS = "amflow-status"
CHAVE_MOTIVO = "amflow-status-reason"
CHAVE_ATUALIZADO = "amflow-updated"

# index.md §1 — "Gravados pela publicação a partir do Hub". Só os dois comandos de
# publicação gravam estes quatro; `set` sempre os recusa (Contrato, linha Erro).
VALORES_HUB = frozenset({"pending_review", "changes_requested", "rejected", "published"})

# index.md §1 — gravado só pela revisão (plano 0019): registra que a revisão passou, e o
# Creator não o declara. `set` o recusa; quem grava é `registrar_revisado`, que o
# `review.py --registrar` chama depois de um `REVISADO`.
VALORES_REVISAO = frozenset({"reviewed"})

# index.md §1 — "Declarados pelo Creator". É o único subconjunto que `set` aceita gravar.
VALORES_CREATOR = STATUS_VALIDOS - VALORES_HUB - VALORES_REVISAO

# plano publish-reviewed-only — onde o identificador do Hub mora, por tipo: em `metadata` para
# skill (só existe depois da 1ª publicação — check.py, comentário de topo), no topo para os
# demais. Só `registrar_publicado` grava este campo; `set` não o toca (não é `amflow-status`).
CHAVE_HUB_ID_SKILL = "amflow-hub-id"
CHAVE_HUB_ID_TOPO = "hub_id"

# index.md §1, coluna Rótulo.
ROTULOS = {
    "in_progress": "Em andamento",
    "paused": "Pausado",
    "blocked": "Bloqueado",
    "reviewed": "Revisado",
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
    "reviewed",
    "in_progress",
    "blocked",
    "pending_review",
    "paused",
    "published",
    "deprecated",
)


def _eh_blocked_ou_familia(valor: str) -> bool:
    """`blocked` e `blocked-RG<nn>` são o mesmo motivo de bloqueio — index.md §3."""
    return valor == "blocked" or bool(BLOQUEIO_REVISAO_RE.match(valor))


def _rotulo(status: str | None) -> str:
    """ROTULOS cobre os nove valores fixos; a família monta o rótulo a partir do gate no id
    (add-blocked-gate-id, index.md §1) — "Bloqueado na revisão (gate <nn>)"."""
    if status is None:
        return "—"
    if status in ROTULOS:
        return ROTULOS[status]
    m = BLOQUEIO_REVISAO_RE.match(status)
    return f"Bloqueado na revisão (gate {int(m.group(1))})" if m else "—"


def _posicao_ordem(status: str | None) -> int:
    """A família ocupa a posição de `blocked` (index.md §4, add-blocked-gate-id)."""
    if status is not None and BLOQUEIO_REVISAO_RE.match(status):
        status = "blocked"
    try:
        return ORDEM_SAIDA.index(status)
    except ValueError:
        return len(ORDEM_SAIDA)

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
    atualizado: str | None = None  # metadata.amflow-updated; vazio ou não-string vira None


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
    cabecalho: list[str]  # fora de linhas para total == len(linhas) continuar valendo


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
    campo_atualizado = fm.metadata.get(CHAVE_ATUALIZADO)
    status, lugar_legado = _resolver_status(
        campo_novo.texto if campo_novo else None,
        campo_legado.texto if campo_legado else None,
    )
    motivo = campo_motivo.texto if campo_motivo else None
    atualizado = campo_atualizado.texto if campo_atualizado and campo_atualizado.texto else None
    return (
        Recurso(tipo, nome, local, caminho, "yaml", _lugar(local), status, lugar_legado, motivo, atualizado),
        None,
    )


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
    valor_atualizado = metadata.get(CHAVE_ATUALIZADO)
    atualizado = valor_atualizado if isinstance(valor_atualizado, str) and valor_atualizado else None
    return (
        Recurso(tipo, nome, local, caminho, "json", _lugar(local), status, lugar_legado, motivo, atualizado),
        None,
    )


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

# Formato da saída (0014-07) — cabeçalho fora de ResultadoListagem.linhas, para que
# total == len(linhas) continue valendo.
_CABECALHO = (
    "| Tipo | Nome | Local | Status | Atualizado | Rótulo |",
    "|---|---|---|---|---|---|",
)

_DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    rotulo = _rotulo(recurso.status)
    atualizado = recurso.atualizado or "(sem data)"
    return (
        f"| {recurso.tipo} | {recurso.nome} | [{recurso.local}]({recurso.local}) "
        f"| {status_txt} | {atualizado} | {rotulo} |"
    )


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


def _chave_data(atualizado: str | None) -> float:
    """Decrescente — mais recente primeiro; ausente, vazia ou fora de YYYY-MM-DD é o pior
    caso, por último dentro do mesmo tipo+status. Dígitos zero-padded ordenam como a data
    (20260912 > 20260101), então negar o inteiro basta — sem precisar validar calendário."""
    if not atualizado or not _DATA_RE.match(atualizado):
        return float("inf")
    return -int(atualizado.replace("-", ""))


def _chave_ordem(recurso: Recurso) -> tuple[str, int, float, str]:
    """`(tipo, posição em ORDEM_SAIDA, chave_data, nome)` — index.md §4 e formato da saída."""
    return (recurso.tipo, _posicao_ordem(recurso.status), _chave_data(recurso.atualizado), recurso.nome)


def _bate_filtro(status: str | None, filtro: str) -> bool:
    """Sem `*` a comparação é exata — `blocked` não pega a família. Com `*` no fim, prefixo:
    `blocked-RG*` pega toda a família e nada mais (add-blocked-gate-id, *A lista e a origem*)."""
    if status is None:
        return False
    if filtro.endswith("*"):
        return status.startswith(filtro[:-1])
    return status == filtro


def listar(projeto: Path, filtros_status: tuple[str, ...] | None = None) -> ResultadoListagem:
    todos, invalidos = varrer(projeto)
    if filtros_status:
        visiveis = [r for r in todos if any(_bate_filtro(r.status, f) for f in filtros_status)]
    else:
        visiveis = list(todos)
    visiveis.sort(key=_chave_ordem)
    return ResultadoListagem(
        linhas=[_formatar_linha(r) for r in visiveis],
        invalidos=invalidos,
        total=len(visiveis),
        rodape=_rodape(todos),
        cabecalho=list(_CABECALHO) if visiveis else [],
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


_SENTINELA_REMOCAO = "\x00REMOVER\x00"


def _fim_do_campo(linhas: list[str], campo) -> int:
    """Índice (0-based, dentro de `linhas`) da primeira linha depois de `campo` — a própria linha
    quando o valor cabe numa linha só; o fim do corpo inteiro quando é block scalar (`|`/`>`),
    porque `campo.linha` só marca onde ele começa. Mesmo critério de parada de
    `check._corpo_do_bloco`, reaplicado aqui porque `Campo` não expõe a linha final — inserir
    logo após `campo.linha` nesse caso split o corpo do block scalar ao meio."""
    inicio = campo.linha - 1  # 0-based
    if not check.BLOCO_RE.match(campo.valor_bruto.strip()):
        return inicio + 1
    indent_chave = len(linhas[inicio]) - len(linhas[inicio].lstrip())
    fim = inicio + 1
    for i in range(inicio + 1, len(linhas)):
        linha = linhas[i]
        if linha.strip() and len(linha) - len(linha.lstrip()) <= indent_chave:
            break
        fim = i + 1
    return fim


def _ponto_insercao_metadata(fm, campo_metadata, linhas: list[str]) -> int:
    """Onde inserir uma linha nova dentro do bloco `metadata:` — depois do corpo inteiro do
    último campo existente, ou logo após a própria chave `metadata:` quando ela ainda não tem
    nenhum filho. Única fonte deste cálculo: `_escrever_yaml` e `_gravar_hub_id` o compartilham,
    em vez de cada um recalcular por conta própria."""
    if not fm.metadata:
        return campo_metadata.linha
    ultimo = max(fm.metadata.values(), key=lambda c: c.linha)
    return _fim_do_campo(linhas, ultimo)


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
    elif campo_motivo is not None and not _eh_blocked_ou_familia(valor):
        # Fecha blocked → in_progress → reviewed com o motivo antigo preso (medido na revisão do
        # 0019). L-04: um motivo em bloco (`|`/`>`) ocupa mais de uma linha e não sabemos apagar
        # essas linhas com segurança por este índice só — a chave fica, em vez de arriscar.
        if not check.BLOCO_RE.match(campo_motivo.valor_bruto.strip()):
            linhas[campo_motivo.linha - 1] = _SENTINELA_REMOCAO

    if campo_metadata is None:
        ponto = _linha_fechamento_frontmatter(linhas)
        linhas[ponto:ponto] = ["metadata:\n"] + novas
    elif novas:
        ponto = _ponto_insercao_metadata(fm, campo_metadata, linhas)
        linhas[ponto:ponto] = novas

    linhas = [l for l in linhas if l != _SENTINELA_REMOCAO]
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
    elif not _eh_blocked_ou_familia(valor):
        # JSON não tem block scalar — L-04 (a linha acima, em _escrever_yaml) não se aplica aqui.
        metadata.pop(CHAVE_MOTIVO, None)
    quebra_final = "\n" if texto.endswith("\n") else ""
    novo_texto = json.dumps(dados, indent=2, ensure_ascii=False) + quebra_final
    recurso.caminho.write_text(novo_texto, encoding="utf-8")


def _gravar(alvo: Recurso, valor: str, motivo: str | None) -> ResultadoSet:
    """Escreve `valor` no recurso — o passo que `atualizar` e `registrar_revisado` compartilham."""
    status_antigo = alvo.status or "(sem status)"

    try:
        if alvo.formato == "yaml":
            _escrever_yaml(alvo, valor, motivo)
        else:
            _escrever_json(alvo, valor, motivo)
    except OSError as exc:
        return ResultadoSet(False, f"recusado: não foi possível gravar {alvo.local} — {exc}")

    return ResultadoSet(True, f"{alvo.tipo}/{alvo.nome}: {status_antigo} → {valor} ({alvo.local})")


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
    if valor in VALORES_REVISAO or BLOQUEIO_REVISAO_RE.match(valor):
        return ResultadoSet(
            False, f"recusado: '{valor}' é gravado pela revisão — rode /amflow-builder:review"
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
    return _gravar(alvo, valor, motivo)


def _origem_valida_da_revisao(status: str | None) -> bool:
    """`in_progress` (o que o `build` deixa) ou qualquer `blocked-RG*` (uma nova revisão recomeça
    do bloqueio anterior — add-blocked-gate-id, decisão 2)."""
    return status == "in_progress" or bool(status and BLOQUEIO_REVISAO_RE.match(status))


def registrar_revisado(projeto: Path, manifesto: Path) -> ResultadoSet:
    """Grava `reviewed` no recurso cujo manifesto é `manifesto` (plano 0019).

    Só o `review.py --registrar` chama isto, depois de um `REVISADO`; `atualizar` recusa o valor. O
    recurso é achado pelo caminho do manifesto, e não por `tipo/nome` como em `atualizar`: quando
    existem a cópia em desenvolvimento e a promovida em `.claude/`, gravar na que a revisão não leu
    marcaria como revisado um arquivo que ninguém revisou.

    Só grava a partir de `in_progress` ou de `blocked-RG*` (add-blocked-gate-id, decisão 2). Qualquer
    outro status é recusado, em vez de sobrescrito — sobretudo os que o Hub grava, que a revisão
    apagaria (`published → reviewed`).
    """
    todos, _ = varrer(projeto)
    alvo = next((r for r in todos if r.caminho.resolve() == manifesto.resolve()), None)
    if alvo is None:
        return ResultadoSet(False, f"recusado: recurso não encontrado — {manifesto}")
    if not _origem_valida_da_revisao(alvo.status):
        return ResultadoSet(
            False,
            f"recusado: 'reviewed' só é gravado a partir de 'in_progress' ou de 'blocked-RG*' — "
            f"o recurso está em '{alvo.status or 'sem status'}'",
        )
    return _gravar(alvo, "reviewed", None)


def registrar_bloqueio(projeto: Path, manifesto: Path, gate: int, motivo: str) -> ResultadoSet:
    """Grava `blocked-RG<gate>` no recurso cujo manifesto é `manifesto` (add-blocked-gate-id).

    Só o `review.py --bloquear` chama isto, em toda parada da revisão que não é `REVISADO`. Não
    refaz a revisão: registra o gate e o motivo que o agent e o Creator observaram — o script é o
    piso, e o agent pode piorar o resultado dele nos gates 3 e 4 por julgamento (L-01, mesmo limite
    do `--registrar` no plano 0019). `review.py` (`GATES`) já recusa gate desconhecido antes de
    chamar esta função, mas o valor final é conferido aqui também, contra a mesma
    `BLOQUEIO_REVISAO_RE` que `check.py` usa para aceitar `blocked-RG<nn>` — sem isso, um `gate` fora
    de 1-99 (ou um chamador direto, fora do `--bloquear`) gravaria um valor que a própria verificação
    de frontmatter rejeitaria na revisão seguinte.

    Mesmas duas origens do `registrar_revisado` — `in_progress` ou `blocked-RG*` —, porque a mesma
    decisão 2 rege os dois escritores: uma nova revisão recomeça do bloqueio anterior, sobrescrevendo
    tanto para `reviewed` quanto para um novo `blocked-RG<nn>`. O motivo vem datado por código
    (`YYYY-MM-DD — texto`) — D6 pedia a data, e data escrita por código não erra.
    """
    if not motivo or not motivo.strip():
        return ResultadoSet(False, "recusado: '--bloquear' exige --motivo")

    valor = f"blocked-RG{gate:02d}"
    if not BLOQUEIO_REVISAO_RE.match(valor):
        return ResultadoSet(False, f"recusado: gate desconhecido — '{gate}' não forma um id válido ({valor})")

    todos, _ = varrer(projeto)
    alvo = next((r for r in todos if r.caminho.resolve() == manifesto.resolve()), None)
    if alvo is None:
        return ResultadoSet(False, f"recusado: recurso não encontrado — {manifesto}")
    if not _origem_valida_da_revisao(alvo.status):
        return ResultadoSet(
            False,
            f"recusado: 'blocked-RG' só é gravado a partir de 'in_progress' ou de 'blocked-RG*' — "
            f"o recurso está em '{alvo.status or 'sem status'}'",
        )

    motivo_datado = f"{date.today().isoformat()} — {motivo.strip()}"
    return _gravar(alvo, valor, motivo_datado)


def _gravar_hub_id(alvo: Recurso, hub_id: str) -> None:
    """Grava `hub_id`, só quando o recurso ainda não tinha um — a atualização reenvia o mesmo
    valor, e não há nada a trocar. Escritor à parte de `_gravar`: o campo mora em
    `metadata.amflow-hub-id` em skill e no topo (`hub_id`) nos demais tipos (plano
    publish-reviewed-only), lugar diferente de `amflow-status`/`amflow-status-reason`, os dois
    campos que `_gravar` conhece."""
    texto = alvo.caminho.read_text(encoding="utf-8")
    fm = check.parsear(texto)
    if fm is None:
        raise OSError("frontmatter ausente ou malformado")
    linhas = texto.splitlines(keepends=True)

    em_metadata = alvo.tipo == "skill"
    campo = fm.metadata.get(CHAVE_HUB_ID_SKILL) if em_metadata else fm.topo.get(CHAVE_HUB_ID_TOPO)
    if campo is not None and campo.texto:
        return  # já tem valor — atualização, nada a gravar

    valor = _valor_yaml(hub_id)
    if campo is not None:
        linhas[campo.linha - 1] = _substituir_valor(linhas[campo.linha - 1], valor)
    elif em_metadata:
        campo_metadata = fm.topo.get("metadata")
        linha_nova = f"  {CHAVE_HUB_ID_SKILL}: {valor}\n"
        if campo_metadata is None:
            ponto = _linha_fechamento_frontmatter(linhas)
            linhas[ponto:ponto] = ["metadata:\n", linha_nova]
        else:
            ponto = _ponto_insercao_metadata(fm, campo_metadata, linhas)
            linhas[ponto:ponto] = [linha_nova]
    else:
        ponto = _linha_fechamento_frontmatter(linhas)
        linhas[ponto:ponto] = [f"{CHAVE_HUB_ID_TOPO}: {valor}\n"]

    alvo.caminho.write_text("".join(linhas), encoding="utf-8")


def _gravar_source(alvo: Recurso, versao: str) -> None:
    """Grava `source: hub/<tipo>/<nome>@<versão>` no topo — todo publish, não só a 1ª submissão,
    porque a versão muda a cada atualização (diferente de `_gravar_hub_id`, que só grava uma
    vez). Skill nunca grava: a norma reserva `amflow-source` só à cópia instalada, nunca à fonte.
    Comportamento restaurado do `publish.md` anterior (Fase 6), que este plano preservou sem
    listar entre as mudanças."""
    if alvo.tipo == "skill":
        return
    texto = alvo.caminho.read_text(encoding="utf-8")
    fm = check.parsear(texto)
    if fm is None:
        raise OSError("frontmatter ausente ou malformado")
    linhas = texto.splitlines(keepends=True)

    valor = _valor_yaml(f"hub/{alvo.tipo}/{alvo.nome}@{versao}")
    campo = fm.topo.get("source")
    if campo is not None:
        linhas[campo.linha - 1] = _substituir_valor(linhas[campo.linha - 1], valor)
    else:
        ponto = _linha_fechamento_frontmatter(linhas)
        linhas[ponto:ponto] = [f"source: {valor}\n"]

    alvo.caminho.write_text("".join(linhas), encoding="utf-8")


def registrar_publicado(projeto: Path, manifesto: Path, hub_id: str, versao: str) -> ResultadoSet:
    """Grava depois do aceite do Hub (`publish.py --registrar`, plano publish-reviewed-only):
    `amflow-status: pending_review` sempre, `source` nos tipos que o levam (todo publish, com a
    versão atual), e o identificador do Hub só quando ainda não havia um.

    Só o `publish.py --registrar` chama isto, e só depois de uma resposta de aceite do Hub — o
    script não confirma isso sozinho, é o agent quem decide se chama, e recusado ali é recusado
    sem gravar nada. Recusa aqui só quando o recurso não é `skill` nem `agent`, fora do escopo da
    publicação (decisão 3 do plano) — os únicos dois tipos que `publish.py` alcança.
    """
    todos, _ = varrer(projeto)
    alvo = next((r for r in todos if r.caminho.resolve() == manifesto.resolve()), None)
    if alvo is None:
        return ResultadoSet(False, f"recusado: recurso não encontrado — {manifesto}")
    if alvo.tipo not in ("skill", "agent"):
        return ResultadoSet(False, f"recusado: '{alvo.tipo}' está fora do escopo da publicação")

    try:
        _gravar_hub_id(alvo, hub_id)
        _gravar_source(alvo, versao)
    except OSError as exc:
        return ResultadoSet(False, f"recusado: não foi possível gravar {alvo.local} — {exc}")

    return _gravar(alvo, "pending_review", None)


# ── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p_list = sub.add_parser("list", help="lista os recursos do projeto e seus status")
    p_list.add_argument("projeto", type=Path)
    p_list.add_argument(
        "--status",
        action="append",
        default=None,
        help="repetível; termina em '*' para curinga de prefixo — ex.: --status in_progress --status 'blocked-RG*'",
    )

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
        filtros = tuple(args.status) if args.status else None
        resultado = listar(projeto, filtros)
        for inv in resultado.invalidos:
            print(f"ERRO {inv.tipo} {inv.local}: {inv.erro}")
        for linha in resultado.cabecalho:
            print(linha)
        for linha in resultado.linhas:
            print(linha)
        print()
        sufixo = f" (status={','.join(filtros)})" if filtros else ""
        print(f"{resultado.total} recurso(s) encontrado(s){sufixo}")
        for linha in resultado.rodape:
            print(linha)
        return 1 if resultado.invalidos else 0

    resultado = atualizar(projeto, args.recurso, args.valor, args.motivo)
    print(resultado.mensagem)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    sys.exit(main())

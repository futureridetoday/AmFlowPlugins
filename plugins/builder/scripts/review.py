#!/usr/bin/env python3
"""`review.py` — a parte determinística da revisão de um recurso antes da publicação.

Roda os quatro portões do agent `resource-reviewer` sobre um recurso do Creator — `skill` ou
`agent` — e devolve o `RESULTADO` provisório, o portão em que parou e a lista de problemas, avisos e
candidatos. O agent só interpreta essa saída: o que é previsível e repetível mora aqui (princípio
*Determinismo em código*), e o que exige julgamento fica com ele — os candidatos do portão 3 e a
correção das informações do portão 4.

Os portões, em sequência. A revisão **para no primeiro que reprova**, e essa regra é deste script:

  1. Template     — o recurso preserva a estrutura mínima que o Builder entrega para o tipo. A
                    declaração fica ao lado do template (`structure.json`), e este script a lê.
  2. Frontmatter  — completo pela norma do tipo, e com o que o Hub exige do `name` e da
                    `description`. Skill: `check.py`. Agent: as regras da declaração.
  3. Funcionamento mínimo — o recurso funciona conforme o que declara, e o bundle passa no que o
                    Hub recusa (tamanho e padrões de conteúdo).
  4. Descrição    — `[tipo]-description.md` tem os blocos do template e informações coerentes.

Saída: uma linha `RESULTADO:` — `REVISADO`, `REPROVADO`, `PENDENTE-FRONTMATTER` ou
`PENDENTE-DESCRICAO` —, seguida de `PORTAO:`, `RECURSO:`, `MOTIVO:` (só na descrição: `ausente` ou
`com-erros`), `PROBLEMAS:` (bloqueiam), `AVISOS:`, `CANDIDATOS:` (o agent decide) e, em skill com
`description` em várias linhas, `PROPOSTA-DESCRIPTION:`. Seção vazia é omitida.

`PENDENTE-*` é o ponto em que o Creator decide se aceita ajuda. O script não pergunta e só escreve
com `--registrar`, e só o `reviewed`: aponta o que falta, e quem pergunta é o comando `review`.

`--registrar` grava `reviewed` no recurso, com o escritor do `status.py`, e só se o resultado é
`REVISADO` e o recurso está em `in_progress` — nos demais o arquivo fica intacto (plano 0019). Fora
de `in_progress` a gravação é recusada, com saída 2. O script refaz a revisão antes de gravar:
o comando o chama depois do `REVISADO` do agent, mas o piso determinístico vale mesmo para quem o
chamar direto. O que o script não refaz é o julgamento do agent — candidatos do portão 3, coerência
do portão 4 —, então quem o chama sem o comando grava `reviewed` num recurso que o agent poderia
reprovar (L-01 do plano). Ao gravar, acrescenta à saída uma linha `REGISTRADO:`.

Cross-repo: nasce aqui, em `scripts/`, e desce a `plugins/builder/scripts/review.py` do
AmFlowPlugins por `vendor.py` — mesmo mecanismo do `check.py` e do `status.py`. A cópia é gerada,
nunca editada do outro lado. Os templates ficam em `plugins/builder/templates/`, e o script os acha
pelo próprio caminho (`../templates`): a variável `CLAUDE_PLUGIN_ROOT` não existe no ambiente do
Bash, nem no de um subagente — só é substituída inline no texto do agent.

Uso:
  review.py <projeto> <local> [--templates <diretório>] [--registrar]

`<local>` é o caminho do manifesto relativo ao projeto, o mesmo que `status.py list` imprime na
coluna Local — ex.: `skills/deep-research/SKILL.md`, `agents/reviewer/reviewer.md`.

Sai com 0 se o resultado provisório é `REVISADO`, 1 nos demais casos, 2 se a chamada não é válida
ou, com `--registrar`, se a gravação foi recusada.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── check.py — reusado, nunca redeclarado ─────────────────────────────────────


def _carregar_check():
    """Carrega `check.py` de onde ele estiver — irmão (plugin, pós-vendor) ou `frontmatter/` (fonte).

    Mesmo desenho do `status.py`: `importlib` por caminho, com o registro em `sys.modules` antes do
    `exec_module`, que o `@dataclass` sob `from __future__ import annotations` exige.
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


def _carregar_status():
    """Carrega `status.py`, irmão deste arquivo — o `--registrar` usa o escritor dele.

    Só sob demanda: quem não registra não paga a carga. Mesmo desenho do `_carregar_check`, com nome
    próprio em `sys.modules`, registrado antes do `exec_module` por causa do `@dataclass`.
    """
    caminho = Path(__file__).resolve().parent / "status.py"
    if not caminho.is_file():
        raise RuntimeError("status.py não encontrado ao lado de review.py")
    spec = importlib.util.spec_from_file_location("builder_status", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


# ── constantes ────────────────────────────────────────────────────────────────

# Modelos do Builder por tipo, relativos à pasta de templates. A declaração da estrutura mínima
# de skill fica ao lado da pasta `skill/`, e não dentro dela: o `build` copia essa pasta inteira
# para todo recurso novo, e um arquivo dentro dela iria parar no bundle publicado.
MODELOS = {
    "skill": {
        "declaracao": "skills/structure.json",
        "manifesto": "skills/skill/SKILL.md",
        "descricao": "skills/skill/skill-description.md",
        "evals": "skills/skill/evals/eval_queries.json",
    },
    "agent": {
        "declaracao": "agents/structure.json",
        "manifesto": "agents/agent.md",
        "descricao": "agents/agent-description.md",
    },
}

# Limites do Hub sobre o que o `publish` envia: por arquivo, na validação da submissão; no total, na
# instalação — o envio aceita o que o `install` depois recusa.
LIMITE_ARQUIVO = 1024 * 1024
LIMITE_BUNDLE = 10 * 1024 * 1024

# Forma do `name` no Hub: começa por letra. A do `check.py` aceita começar por dígito.
_NOME_HUB_RE = re.compile(r"[a-z][a-z0-9-]*")
_NOME_FORMA_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")

_BLOCO_RE = re.compile(r"[|>][-+]?\d*")
_COMENTARIO_RE = re.compile(r"<!--[\s\S]*?-->")
_MARCADOR_RE = re.compile(r"<[^<>\n]+>|\[[^\[\]\n]{2,}\]")
_TAG_RE = re.compile(r"</?\w+>")

TIPOS_DEPENDENCIA_HUB = frozenset({"skill", "agent", "command", "hook"})

# Ferramentas do Claude Code que um corpo de agent costuma citar. Só estas entram no cruzamento
# com o campo `tools`.
FERRAMENTAS = ("Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "Skill", "WebFetch", "WebSearch")
_FERRAMENTA_RE = re.compile(
    r"`(?:{n})\b[^`]*`|\b(?:ferramentas?|tools?)\s+`?(?:{n})\b|\b(?:{n})\(".format(n="|".join(FERRAMENTAS))
)

# A norma diz "cerca de 80 caracteres" para um item de Limites: o aviso só dispara bem acima disso,
# para não virar ruído em frase que passou pouco.
LIMITE_ITEM_LIMITES = 100
MAX_ITENS_LIMITES = 5

# ── padrões do Hub ────────────────────────────────────────────────────────────
#
# Espelham, um a um e na mesma ordem, as quatro listas do verificador do Hub (`validate.ts`). O
# texto de cada regex é o do literal em JavaScript, sem tocar — um teste extrai as regexes de lá e
# compara com estas, para as duas não divergirem em silêncio. Cada item é `(fonte, flags)`, ou
# `(fonte, flags, rótulo)` onde o Hub tem rótulo.

DANGEROUS_PATTERNS = (
    (r"rm\s+-rf\s+\/", ""),
    (r"curl[^|]*\|\s*(ba)?sh", ""),
    (r"wget[^|]*\|\s*(ba)?sh", ""),
    (r"\beval\s*\(", ""),
    (r"\bexec\s*\(", ""),
    (r"os\.system\s*\(", ""),
    (r"subprocess\.(call|run|Popen)\s*\(", ""),
)

CREDENTIAL_PATTERNS = (
    (r"sk_live_[0-9a-zA-Z]{16,}", "", "chave secreta Stripe"),
    (r"\bAKIA[0-9A-Z]{16}\b", "", "AWS access key"),
    (r"\bghp_[0-9A-Za-z]{36}\b", "", "GitHub token"),
    (r"xox[baprs]-[0-9A-Za-z]{8,}-[0-9A-Za-z]{8,}", "", "Slack token"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "", "Google API key"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "", "chave privada"),
)

PROMPT_INJECTION_PATTERNS = (
    (r"ignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above)\s+instructions", "i"),
    (r"disregard\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|system)\s+(?:instructions|prompts?|messages?)", "i"),
)

SUSPICIOUS_URL_PATTERNS = (
    (r"https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "", "URL com IP literal"),
    (r"\bdata:text\/html", "i", "data URI HTML"),
    (r"https?:\/\/(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd)\/", "i", "encurtador de URL"),
)

# `\s` do JavaScript inclui o espaço sem quebra, os espaços Unicode e o BOM; o do Python com
# `re.ASCII` só os ASCII. Sem trocar, `rm<NBSP>-rf /` escaparia daqui e o Hub o recusaria.
_ESPACO_JS = r"[\t\n\v\f\r    -     　﻿]"


def compilar_js(fonte: str, flags: str) -> re.Pattern[str]:
    """Compila o texto de uma regex JavaScript com a semântica que ela tem lá.

    `re.ASCII`: `\\b`, `\\d` e `\\w` do Python são Unicode por padrão e os do JavaScript são ASCII —
    sem a flag, `çeval(x)` escapa da regra de `eval` e `http://١٢٣.4.5.6/` seria barrada como IP
    literal, ao contrário do Hub. `\\s` é trocado pela classe do JavaScript; nenhum padrão o usa
    dentro de classe de caracteres (o teste confere).
    """
    fonte_py = fonte.replace(r"\s", _ESPACO_JS)
    return re.compile(fonte_py, re.ASCII | (re.IGNORECASE if "i" in flags else 0))


def _padroes_hub() -> list[tuple[re.Pattern[str], str]]:
    """As quatro listas achatadas em `(regex, rótulo)`, com o rótulo que vai para o relatório."""
    saida: list[tuple[re.Pattern[str], str]] = []
    for lista, moldura, padrao in (
        (DANGEROUS_PATTERNS, "{}", "comando potencialmente perigoso"),
        (CREDENTIAL_PATTERNS, "credencial hardcoded ({})", None),
        (PROMPT_INJECTION_PATTERNS, "{}", "possível prompt injection"),
        (SUSPICIOUS_URL_PATTERNS, "URL suspeita ({})", None),
    ):
        for item in lista:
            rotulo = moldura.format(item[2] if len(item) == 3 else padrao)
            saida.append((compilar_js(item[0], item[1]), rotulo))
    return saida


PADROES_HUB = _padroes_hub()

# ── tipos de dado ─────────────────────────────────────────────────────────────


class ErroUso(Exception):
    """Chamada inválida: o script não chega a revisar. Sai com 2, mensagem em stderr."""


@dataclass
class Alvo:
    tipo: str
    nome: str  # nome da pasta do recurso
    projeto: Path
    pasta: Path
    manifesto: Path
    solto: bool = False  # agent em arquivo solto, sem pasta


@dataclass
class Modelo:
    declaracao: dict
    manifesto: str
    descricao: str
    evals: dict | None = None


@dataclass
class Bundle:
    """O que o `publish` vai enviar (regra provisória) e o que ele deixa de fora, com o motivo."""

    selecionados: dict[str, str] = field(default_factory=dict)  # caminho relativo → conteúdo
    tamanhos: dict[str, int] = field(default_factory=dict)  # caminho relativo → bytes em UTF-8
    omitidos: dict[str, str] = field(default_factory=dict)  # caminho relativo → motivo


@dataclass
class Relatorio:
    tipo: str
    nome: str
    local: str
    versao: str | None = None
    resultado: str = "REVISADO"
    portao: int = 4
    motivo: str | None = None
    problemas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    candidatos: list[str] = field(default_factory=list)
    proposta_description: str | None = None

    def parar(self, resultado: str, portao: int, motivo: str | None = None) -> "Relatorio":
        self.resultado, self.portao, self.motivo = resultado, portao, motivo
        return self


# ── helpers de JavaScript — o que o Hub faz com o texto ───────────────────────

_ESPACOS_TRIM = (
    "\t\n\v\f\r   "
    + "".join(chr(c) for c in range(0x2000, 0x200B))
    + "    　﻿"
)


def js_trim(texto: str) -> str:
    """`String.prototype.trim` do JavaScript: inclui o BOM e os espaços Unicode."""
    return texto.strip(_ESPACOS_TRIM)


def linhas_js(texto: str) -> list[str]:
    """Linhas como o `^`/`$` multilinha do JavaScript as enxerga: `\\n`, `\\r`, `\\u2028`, `\\u2029`."""
    return re.split(r"\r\n|[\n\r  ]", texto)


def tirar_comentarios(texto: str) -> str:
    """Remove os comentários HTML, como o Hub faz antes de validar a descrição."""
    return _COMENTARIO_RE.sub("", texto)


def _mascarar_comentarios(texto: str) -> str:
    """Troca o miolo dos comentários por espaço, preservando as quebras — a numeração de linha fica."""
    return _COMENTARIO_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), texto)


# ── leitura do manifesto ──────────────────────────────────────────────────────


def _corpo(texto: str) -> tuple[list[str], int]:
    """Linhas do corpo (depois do frontmatter) e o deslocamento que leva ao número de linha do arquivo."""
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return linhas, 0
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            return linhas[i + 1 :], i + 1
    return linhas, 0


def _vazio(campo) -> bool:
    return campo is None or campo.texto in ("", "[]", "{}")


def _descricao_em_varias_linhas(bloco: list[str]) -> str | None:
    """A `description` em uma linha só, quando o campo ocupa várias; `None` quando já cabe em uma.

    O Hub lê o campo por regex de uma linha: `|`, `>-` e o texto quebrado chegam ao catálogo como
    `|`, `>-` ou só a primeira linha. O `check.py` aceita as três formas.
    """
    for i, linha in enumerate(bloco):
        m = re.match(r"^description:[ \t]*(.*?)[ \t]*$", linha)
        if not m:
            continue
        valor = m.group(1)
        continuacao: list[str] = []
        for seguinte in bloco[i + 1 :]:
            if not seguinte.strip():
                continue
            if seguinte[0] in " \t":
                continuacao.append(seguinte.strip())
            else:
                break
        em_bloco = bool(_BLOCO_RE.fullmatch(valor))
        if not em_bloco and not continuacao:
            return None
        texto = " ".join(([] if em_bloco or not valor else [valor]) + continuacao)
        if len(texto) >= 2 and texto[0] in "\"'" and texto[-1] == texto[0]:
            texto = texto[1:-1]
        return texto
    return None


def _aspas(texto: str) -> str:
    """Entre aspas duplas; simples quando o texto tem duplas; cru quando tem as duas."""
    if '"' not in texto:
        return f'"{texto}"'
    if "'" not in texto:
        return f"'{texto}'"
    return texto


# ── identificação e modelos ───────────────────────────────────────────────────

_LOCAL_SKILL = re.compile(r"^(\.claude/)?skills/([^/]+)/SKILL\.md$")
_LOCAL_AGENT = re.compile(r"^(\.claude/)?agents/([^/]+)/([^/]+)\.md$")
_LOCAL_AGENT_SOLTO = re.compile(r"^(\.claude/)?agents/([^/]+)\.md$")


def identificar(projeto: Path, local: str) -> Alvo:
    """O recurso a partir do caminho do manifesto — o que o comando `review` recebeu do `status.py`."""
    local = local.replace("\\", "/")
    if Path(local).is_absolute():
        try:
            local = str(Path(local).resolve().relative_to(projeto.resolve()))
        except ValueError:
            raise ErroUso(f"o caminho {local} está fora do projeto {projeto}")

    m = _LOCAL_SKILL.match(local)
    if m:
        pasta = projeto / (m.group(1) or "") / "skills" / m.group(2)
        return Alvo("skill", m.group(2), projeto, pasta, projeto / local)

    m = _LOCAL_AGENT.match(local)
    if m:
        pasta = projeto / (m.group(1) or "") / "agents" / m.group(2)
        return Alvo("agent", m.group(2), projeto, pasta, projeto / local)

    m = _LOCAL_AGENT_SOLTO.match(local)
    if m and not m.group(2).endswith(("-description", "-workflow")):
        pasta = projeto / (m.group(1) or "") / "agents" / m.group(2)
        return Alvo("agent", m.group(2), projeto, pasta, projeto / local, solto=True)

    raise ErroUso(
        f"'{local}' não é o manifesto de uma skill ou de um agent — esperado skills/<nome>/SKILL.md "
        "ou agents/<nome>/<nome>.md. A revisão cobre só esses dois tipos"
    )


def carregar_modelo(templates: Path, tipo: str) -> Modelo:
    caminhos = MODELOS[tipo]

    def ler(relativo: str) -> str:
        arquivo = templates / relativo
        try:
            return arquivo.read_text(encoding="utf-8")
        except OSError as exc:
            raise ErroUso(f"template ausente ou ilegível: {arquivo} — {exc}")

    try:
        declaracao = json.loads(ler(caminhos["declaracao"]))
        evals = json.loads(ler(caminhos["evals"])) if "evals" in caminhos else None
    except json.JSONDecodeError as exc:
        raise ErroUso(f"template com JSON inválido em {templates} — {exc}")
    return Modelo(declaracao, ler(caminhos["manifesto"]), ler(caminhos["descricao"]), evals)


def _relativo(alvo: Alvo, caminho: Path) -> str:
    return caminho.relative_to(alvo.projeto).as_posix()


# ── portão 1 — template ───────────────────────────────────────────────────────


def _titulos_h2(linhas: list[str]) -> set[str]:
    """Títulos `## ` fora de cerca de código e de comentário."""
    titulos, em_cerca = set(), False
    for linha in _mascarar_comentarios("\n".join(linhas)).split("\n"):
        if linha.lstrip().startswith("```"):
            em_cerca = not em_cerca
            continue
        m = None if em_cerca else re.fullmatch(r"## (.+?)\s*", linha)
        if m:
            titulos.add(m.group(1))
    return titulos


def portao_template(alvo: Alvo, decl: dict) -> list[str]:
    """Estrutura mínima: os arquivos e as seções H2 que a declaração exige. O documento de
    descrição não entra: a ausência dele é assunto do portão 4, onde há oferta de criação."""
    problemas = []
    for modelo in decl["arquivos"]:
        arquivo = alvo.pasta / modelo.replace("<name>", alvo.nome)
        if not arquivo.is_file():
            problemas.append(f"arquivo obrigatório ausente: {_relativo(alvo, arquivo)}")
    if alvo.manifesto.is_file():
        corpo, _ = _corpo(alvo.manifesto.read_text(encoding="utf-8"))
        presentes = _titulos_h2(corpo)
        problemas += [f"seção obrigatória ausente: ## {s}" for s in decl["secoes"] if s not in presentes]
    return problemas


# ── portão 2 — frontmatter ────────────────────────────────────────────────────


def _v1(alvo: Alvo, campo_nome) -> list[str]:
    """V1 — o Hub recusa o `name` que começa por número, e o `check.py` o aceita. Falha definitiva:
    o nome é a identidade do recurso (pasta, `name`, título da descrição, referências no corpo), e
    renomear é decisão do Creator, sem oferta de ajuda."""
    origens: dict[str, list[str]] = {alvo.nome: ["diretório"]}
    if campo_nome is not None and campo_nome.texto:
        origens.setdefault(campo_nome.texto, []).append("name")
    return [
        f"[V1] {' e '.join(onde)} '{valor}' começa por número — o Hub recusa (o nome deve começar por "
        "letra: [a-z][a-z0-9-]*). Renomear é decisão do Creator: a pasta, o `name`, o título da "
        "descrição e as referências no corpo"
        for valor, onde in origens.items()
        if _NOME_FORMA_RE.fullmatch(valor) and not _NOME_HUB_RE.fullmatch(valor)
    ]


def _campo(fm, chave: str):
    if chave.startswith("metadata."):
        return fm.metadata.get(chave[len("metadata.") :])
    return fm.topo.get(chave)


def _frontmatter_agent(alvo: Alvo, fm, decl: dict) -> tuple[list[str], list[str]]:
    """As regras de frontmatter de agent, lidas da declaração: o que bloqueia, o que avisa e o
    formato de cada campo. `name` igual ao diretório e o domínio do status são regras de código."""
    problemas: list[str] = []
    avisos: list[str] = []
    dominio = check.STATUS_VALIDOS | check.STATUS_LEGADO
    for lista, severidade in ((decl["frontmatter"]["bloqueiam"], problemas), (decl["frontmatter"]["avisam"], avisos)):
        for chave, formato in lista.items():
            campo = _campo(fm, chave)
            if _vazio(campo):
                severidade.append(f"campo {'obrigatório' if severidade is problemas else 'recomendado'} ausente ou vazio: {chave}")
            elif chave == "metadata.amflow-status":
                if campo.texto not in dominio:
                    severidade.append(f"{chave} fora do domínio: '{campo.texto}' — use um de {', '.join(sorted(check.STATUS_VALIDOS))}")
            elif formato and not re.fullmatch(formato, campo.texto):
                severidade.append(f"{chave} fora do formato: '{campo.texto}'")
            elif chave == "name" and campo.texto != alvo.nome:
                severidade.append(f"name '{campo.texto}' diferente do diretório '{alvo.nome}'")
    if "status" in fm.topo:
        avisos.append("`status` no topo do frontmatter é legado — o estado mora em `metadata.amflow-status`")
    for chave in ("tags", "dependencies"):
        if not _vazio(fm.topo.get(chave)):
            avisos.append(
                f"[V11] `{chave}` no topo não chega ao catálogo: o Hub só lê `metadata.amflow-{chave}`"
            )
    return problemas, avisos


def _marcadores_da_descricao(modelo: Modelo, fm) -> list[str]:
    """Linhas da `description` de agent que ainda são as do template — texto por preencher."""
    campo = fm.topo.get("description")
    if campo is None:
        return []
    fm_modelo = check.parsear(modelo.manifesto)
    if fm_modelo is None or "description" not in fm_modelo.topo:
        return []
    linhas_modelo = {
        l.strip() for l in fm_modelo.topo["description"].texto.splitlines() if _MARCADOR_RE.search(l) and not _TAG_RE.fullmatch(l.strip())
    }
    return [l.strip() for l in campo.texto.splitlines() if l.strip() in linhas_modelo]


def portao_frontmatter(alvo: Alvo, texto: str, modelo: Modelo) -> tuple[list[str], list[str], list[str], str | None]:
    """`(problemas, definitivos, avisos, proposta)`. `definitivos` (V1) reprovam sem oferta de ajuda."""
    fm = check.parsear(texto)
    if fm is None:
        return ["frontmatter ausente ou malformado — sem '---' de abertura e fechamento"], [], [], None

    problemas: list[str] = []
    avisos: list[str] = []
    definitivos = _v1(alvo, fm.topo.get("name"))
    proposta = _descricao_em_varias_linhas(check.extrair_bloco(texto) or [])

    if alvo.tipo == "skill":
        for arquivo, violacoes in check.verificar_skill(alvo.pasta).items():
            problemas += [f"{arquivo}: {v}" for v in violacoes]
        campo_dep = fm.metadata.get("amflow-dependencies")
        for entrada in (campo_dep.texto.split() if campo_dep else []):
            tipo_dep = entrada.split("@")[0].split("/")[0]
            if "/" in entrada and tipo_dep not in TIPOS_DEPENDENCIA_HUB:
                avisos.append(f"[V12] dependência '{entrada}' de tipo '{tipo_dep}' — o Hub a descarta em silêncio")
    else:
        problemas, avisos = _frontmatter_agent(alvo, fm, modelo.declaracao)
        problemas += [f"description ainda é o texto do template: {l}" for l in _marcadores_da_descricao(modelo, fm)]

    if proposta is not None:
        if alvo.tipo == "skill":
            problemas.append(
                "[V10] `description` ocupa mais de uma linha — o Hub a lê por regex de uma linha, e o "
                "catálogo recebe só a primeira (`|` ou `>-` no caso de bloco)"
            )
        else:
            avisos.append(
                "[V10] `description` ocupa mais de uma linha — o Hub a lê por regex de uma linha, e o "
                "catálogo recebe só a primeira"
            )
    return problemas, definitivos, avisos, (f"description: {_aspas(proposta)}" if alvo.tipo == "skill" and proposta else None)


# ── portão 3 — funcionamento mínimo ───────────────────────────────────────────


def montar_bundle(pasta: Path) -> Bundle:
    """O conjunto de arquivos que o `publish` vai enviar. **Regra provisória**: os arquivos da pasta
    do recurso, menos `evals/`, os vazios e os que não são UTF-8 — o `content` viaja como string."""
    bundle = Bundle()
    for arquivo in sorted(pasta.rglob("*")):
        if not arquivo.is_file():
            continue
        relativo = arquivo.relative_to(pasta).as_posix()
        if relativo.startswith("evals/"):
            bundle.omitidos[relativo] = "`evals/` não vai no bundle"
            continue
        dados = arquivo.read_bytes()
        try:
            conteudo = dados.decode("utf-8")
        except UnicodeDecodeError:
            bundle.omitidos[relativo] = "não é UTF-8, e o conteúdo viaja como texto"
            continue
        if not js_trim(conteudo):
            bundle.omitidos[relativo] = "vazio — o Hub recusaria o bundle inteiro se ele fosse enviado"
            continue
        bundle.selecionados[relativo] = conteudo
        bundle.tamanhos[relativo] = len(dados)
    return bundle


def _regras_do_hub(bundle: Bundle) -> list[str]:
    """V7, V14 e V8 — o que o Hub recusa no bundle, sobre todos os arquivos enviados, prosa incluída."""
    problemas = []
    for relativo, tamanho in bundle.tamanhos.items():
        if tamanho > LIMITE_ARQUIVO:
            problemas.append(f"[V7] {relativo}: {tamanho} bytes, acima do limite de {LIMITE_ARQUIVO // 1024 // 1024} MB por arquivo")
    total = sum(bundle.tamanhos.values())
    if total > LIMITE_BUNDLE:
        problemas.append(f"[V14] bundle com {total} bytes, acima do limite de {LIMITE_BUNDLE // 1024 // 1024} MB — o envio aceita e a instalação recusa")
    for relativo, conteudo in bundle.selecionados.items():
        for regex, rotulo in PADROES_HUB:
            if regex.search(conteudo):
                problemas.append(f"[V8] {relativo}: {rotulo}")
    return problemas


def _sintaxe(pasta: Path, avisos: list[str]) -> list[str]:
    """Os scripts do recurso compilam — Python em memória, para não deixar `.pyc` ao lado do script
    do Creator; shell por `bash -n`."""
    problemas = []
    for arquivo in sorted(pasta.rglob("*.py")):
        relativo = arquivo.relative_to(pasta).as_posix()
        if relativo.startswith("evals/"):
            continue
        try:
            compile(arquivo.read_text(encoding="utf-8"), str(arquivo), "exec")
        except (SyntaxError, ValueError) as exc:
            linha = f" linha {exc.lineno}" if isinstance(exc, SyntaxError) and exc.lineno else ""
            problemas.append(f"[sintaxe] {relativo}{linha}: {getattr(exc, 'msg', exc)}")
        except UnicodeDecodeError:
            continue  # arquivo binário: o bundle já o avisa como omitido
    bash = shutil.which("bash")
    for arquivo in sorted(pasta.rglob("*.sh")):
        relativo = arquivo.relative_to(pasta).as_posix()
        if bash is None:
            avisos.append(f"bash não encontrado — a sintaxe de {relativo} não foi conferida")
            continue
        resultado = subprocess.run([bash, "-n", str(arquivo)], capture_output=True, text=True, timeout=30)
        if resultado.returncode != 0:
            detalhe = (resultado.stderr.strip().splitlines() or ["erro de sintaxe"])[0]
            problemas.append(f"[sintaxe] {relativo}: {detalhe}")
    return problemas


def _marcadores_do_corpo(texto: str, modelo: Modelo) -> list[str]:
    """O corpo sem marcador de template por preencher: nenhuma linha dele é, palavra por palavra, uma
    linha de placeholder do modelo, e sobra algum conteúdo além do esqueleto."""
    corpo_modelo, _ = _corpo(modelo.manifesto)
    placeholders = {
        l.strip() for l in _mascarar_comentarios("\n".join(corpo_modelo)).split("\n") if _MARCADOR_RE.search(l)
    }
    corpo, deslocamento = _corpo(texto)
    problemas, com_conteudo = [], False
    for numero, linha in enumerate(_mascarar_comentarios("\n".join(corpo)).split("\n"), start=deslocamento + 1):
        limpa = linha.strip()
        if not limpa or limpa.startswith("```"):
            continue
        if limpa in placeholders:
            problemas.append(f"[template] linha {numero}: marcador de template por preencher — `{limpa}`")
        elif not limpa.startswith("#"):
            com_conteudo = True
    if not com_conteudo:
        problemas.append("[template] o corpo não tem conteúdo além do esqueleto do template")
    return problemas


def _evals(alvo: Alvo, nome: str, modelo: Modelo) -> list[str]:
    """`evals/eval_queries.json` preenchido: `skill_name` real, `description_under_test` e ao menos um
    near-miss — caso com `should_trigger: false` que não seja o texto do template."""
    arquivo = alvo.pasta / "evals" / "eval_queries.json"
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"[evals] evals/eval_queries.json ilegível — {exc}"]
    problemas = []
    if dados.get("skill_name") != nome:
        problemas.append(f"[evals] skill_name '{dados.get('skill_name')}' diferente do nome da skill '{nome}'")
    if not str(dados.get("description_under_test") or "").strip():
        problemas.append("[evals] description_under_test vazio")
    textos_modelo = {q.get("query") for q in (modelo.evals or {}).get("queries", [])}
    near_miss = [
        q for q in dados.get("queries", []) if q.get("should_trigger") is False and q.get("query") not in textos_modelo
    ]
    if not near_miss:
        problemas.append("[evals] nenhum near-miss (`should_trigger: false`) além dos textos do template")
    return problemas


def _citacoes(texto: str) -> list[tuple[int, str]]:
    """Arquivos citados no corpo — em crase ou em link, com uma barra e extensão. Fora de cerca de
    código: o que está lá é exemplo de comando, e casar todo token dali só produziria ruído."""
    corpo, deslocamento = _corpo(texto)
    citados, vistos, em_cerca = [], set(), False
    for numero, linha in enumerate(_mascarar_comentarios("\n".join(corpo)).split("\n"), start=deslocamento + 1):
        if linha.lstrip().startswith("```"):
            em_cerca = not em_cerca
            continue
        if em_cerca:
            continue
        for token in re.findall(r"`([^`\n]+)`", linha) + re.findall(r"\]\(([^)\s]+)\)", linha):
            token = re.sub(r":\d+(?:-\d+)?$", "", token)
            if token in vistos or re.search(r"[<>$*?{}|~ @#]|://", token) or token.startswith("/"):
                continue
            if "/" in token and re.search(r"\.[A-Za-z0-9]{1,6}$", token.rsplit("/", 1)[-1]):
                vistos.add(token)
                citados.append((numero, token))
    return citados


def _candidatos_arquivos(alvo: Alvo, texto: str, bundle: Bundle) -> list[str]:
    candidatos = []
    for numero, token in _citacoes(texto):
        dentro = (alvo.pasta / token).resolve()
        try:
            relativo = dentro.relative_to(alvo.pasta.resolve()).as_posix()
        except ValueError:
            relativo = None
        if relativo is not None and dentro.is_file():
            if relativo in bundle.omitidos:
                candidatos.append(
                    f"[arquivo-citado] linha {numero}: `{token}` existe, mas o bundle o omite ({bundle.omitidos[relativo]})"
                )
        elif (alvo.projeto / token).resolve().is_file() or relativo is None:
            candidatos.append(
                f"[arquivo-citado] linha {numero}: `{token}` fica fora da pasta do recurso — não entra no bundle, "
                "e o comprador recebe a referência quebrada"
            )
        else:
            candidatos.append(f"[arquivo-citado] linha {numero}: `{token}` não existe na pasta do recurso nem no projeto")
    return candidatos


def _candidatos_ferramentas(texto: str, fm) -> list[str]:
    """Ferramentas citadas no corpo de um agent que `tools` não lista. Sem `tools`, o agent herda
    tudo, e não há o que cruzar."""
    campo = fm.topo.get("tools") if fm else None
    if campo is None:
        return []
    permitidas = {p.strip().split("(")[0] for p in campo.texto.split(",") if p.strip()}
    corpo, deslocamento = _corpo(texto)
    candidatos, vistas = [], set()
    for numero, linha in enumerate(_mascarar_comentarios("\n".join(corpo)).split("\n"), start=deslocamento + 1):
        for achado in _FERRAMENTA_RE.finditer(linha):
            nome = re.search("|".join(FERRAMENTAS), achado.group(0)).group(0)
            if nome not in permitidas and nome not in vistas:
                vistas.add(nome)
                candidatos.append(
                    f"[ferramenta-citada] linha {numero}: `{nome}` aparece no corpo e não está em `tools` ({campo.texto})"
                )
    return candidatos


def portao_funcionamento(alvo: Alvo, texto: str, modelo: Modelo, nome: str, fm) -> tuple[list[str], list[str], list[str]]:
    """`(problemas, avisos, candidatos)`. Os problemas são falhas definitivas; os candidatos, o que o
    agent decide."""
    bundle = montar_bundle(alvo.pasta)
    avisos = [
        f"{relativo}: omitido do bundle — {motivo}"
        for relativo, motivo in bundle.omitidos.items()
        if not relativo.startswith("evals/")
    ]
    problemas = _sintaxe(alvo.pasta, avisos)
    problemas += _marcadores_do_corpo(texto, modelo)
    if alvo.tipo == "skill":
        problemas += _evals(alvo, nome, modelo)
    problemas += _regras_do_hub(bundle)
    candidatos = _candidatos_arquivos(alvo, texto, bundle)
    if alvo.tipo == "agent":
        candidatos += _candidatos_ferramentas(texto, fm)
    return problemas, avisos, candidatos


# ── portão 4 — descrição ──────────────────────────────────────────────────────


def secoes_do_modelo(descricao_modelo: str) -> list[tuple[str, bool]]:
    """`(título, opcional)` de cada `## ` do modelo, na ordem. Opcional é a seção cujo comentário abre
    com `Opcional.` — a marcação que os modelos já trazem."""
    mascarado = _mascarar_comentarios(descricao_modelo)
    titulos = [(m.end(), m.start(), m.group(1).strip()) for m in re.finditer(r"^## (.+)$", mascarado, re.M)]
    secoes = []
    for i, (fim, _, titulo) in enumerate(titulos):
        limite = titulos[i + 1][1] if i + 1 < len(titulos) else len(descricao_modelo)
        opcional = re.match(r"\s*<!--\s*Opcional\.", descricao_modelo[fim:limite]) is not None
        secoes.append((titulo, opcional))
    return secoes


def _secoes_do_documento(conteudo: str) -> list[tuple[str, str]]:
    """`(título, corpo)` de cada `## ` — sem tratar cerca de código, como o Hub: um `## Passo 1`
    dentro de um bloco de código conta como seção."""
    secoes: list[tuple[str, list[str]]] = []
    for linha in linhas_js(conteudo):
        m = re.fullmatch(r"## (.+)", linha)
        if m:
            secoes.append((js_trim(m.group(1)), []))
        elif secoes:
            secoes[-1][1].append(linha)
    return [(titulo, "\n".join(corpo)) for titulo, corpo in secoes]


def validar_descricao(bruto: str, nome: str, versao: str, secoes: list[tuple[str, bool]]) -> list[str]:
    """As seis regras do verificador do Hub (`validateDescriptionDoc`) sobre o documento, mais a
    exigência de conteúdo nas seções obrigatórias. Devolve todas as falhas, não só a primeira."""
    conteudo = tirar_comentarios(bruto)
    erros = []
    titulo = next((l for l in conteudo.split("\n") if js_trim(l)), None)
    if titulo is None or js_trim(titulo) != f"# {nome}":
        erros.append(f'o título deve ser exatamente "# {nome}" — encontrado: {js_trim(titulo) if titulo else "(vazio)"}')

    declarada = next(
        (m.group(1) for l in linhas_js(conteudo) if (m := re.fullmatch(r"Versão (\d+\.\d+\.\d+)", l, re.ASCII))),
        None,
    )
    if declarada is None:
        erros.append('falta a linha de versão no formato "Versão X.Y.Z"')
    elif declarada != versao:
        erros.append(f"a versão declarada ({declarada}) diverge da versão do recurso ({versao})")

    documento = _secoes_do_documento(conteudo)
    encontradas = [t for t, _ in documento]
    conhecidas = [t for t, _ in secoes]
    desconhecidas = [t for t in encontradas if t not in conhecidas]
    if desconhecidas:
        erros.append(f"seção com título fora do padrão: {', '.join(desconhecidas)}")
    ausentes = [t for t, opcional in secoes if not opcional and t not in encontradas]
    if ausentes:
        erros.append(f"seção obrigatória ausente: {', '.join(ausentes)}")
    esperada = [t for t in conhecidas if t in encontradas]
    if not desconhecidas and encontradas != esperada:
        erros.append(f"seções fora de ordem — esperado: {' → '.join(esperada)}; encontrado: {' → '.join(encontradas)}")

    opcionais = {t for t, opcional in secoes if opcional}
    erros += [
        f"seção obrigatória sem conteúdo: {t}" for t, corpo in documento if t in conhecidas and t not in opcionais and not corpo.strip()
    ]
    return erros


def _avisos_da_descricao(pasta: Path, conteudo: str, secoes: list[tuple[str, bool]]) -> list[str]:
    """Regras de tamanho e de presença das seções opcionais — só aviso: o gate verifica estrutura."""
    avisos = []
    opcionais = {t for t, opcional in secoes if opcional}
    for titulo, corpo in _secoes_do_documento(conteudo):
        linhas = [l for l in corpo.split("\n") if l.strip()]
        if titulo in opcionais and not linhas:
            avisos.append(f"seção opcional vazia: {titulo} — sem o que dizer, remova a seção inteira")
        elif titulo == "Fundamentação" and len(linhas) > 1:
            avisos.append("Fundamentação deve ser uma linha só, com nomes — sem explicação")
        elif titulo == "Base de conhecimento":
            dados = [a for d in ("references", "assets") if (pasta / d).is_dir() for a in (pasta / d).rglob("*") if a.is_file() and not a.name.startswith(".")]
            if not dados:
                avisos.append("Base de conhecimento sem `references/` ou `assets/` com arquivos de dados — remova a seção")
        elif titulo == "Limites":
            itens = [re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", l) for l in linhas if re.match(r"^\s*(?:[-*]|\d+\.)\s+", l)]
            if len(itens) > MAX_ITENS_LIMITES:
                avisos.append(f"Limites tem {len(itens)} itens — a norma pede até {MAX_ITENS_LIMITES}")
            longos = [i for i in itens if len(i) > LIMITE_ITEM_LIMITES]
            if longos:
                avisos.append(f"Limites tem {len(longos)} item(ns) com mais de {LIMITE_ITEM_LIMITES} caracteres — uma frase curta cada")
    return avisos


def portao_descricao(alvo: Alvo, nome: str, versao: str, modelo: Modelo) -> tuple[str | None, list[str], list[str]]:
    """`(motivo, erros, avisos)`. `motivo` é `None` quando a descrição passa, `ausente` quando o documento
    não existe ou é o template intocado, e `com-erros` nos demais casos."""
    arquivo = alvo.pasta / f"{alvo.tipo}-description.md"
    relativo = _relativo(alvo, arquivo)
    if not arquivo.is_file():
        return "ausente", [f"{relativo} não existe"], []
    bruto = arquivo.read_text(encoding="utf-8")
    conteudo = tirar_comentarios(bruto)
    documento = _secoes_do_documento(conteudo)
    if not any(corpo.strip() for _, corpo in documento):
        return "ausente", [f"{relativo} não tem conteúdo em nenhuma seção — é o template intocado"], []
    secoes = secoes_do_modelo(modelo.descricao)
    erros = [f"{relativo}: {e}" for e in validar_descricao(bruto, nome, versao, secoes)]
    avisos = [f"{relativo}: {a}" for a in _avisos_da_descricao(alvo.pasta, conteudo, secoes)]
    return ("com-erros" if erros else None), erros, avisos


# ── a revisão ─────────────────────────────────────────────────────────────────


def _versao(fm, tipo: str) -> str | None:
    campo = fm.metadata.get("amflow-version") if tipo == "skill" else fm.topo.get("version")
    return campo.texto if campo else None


def revisar(projeto: Path, local: str, templates: Path) -> Relatorio:
    alvo = identificar(projeto, local)
    modelo = carregar_modelo(templates, alvo.tipo)
    rel = Relatorio(alvo.tipo, alvo.nome, local)

    # 1 — template
    rel.problemas = portao_template(alvo, modelo.declaracao)
    if rel.problemas:
        return rel.parar("REPROVADO", 1)

    texto = alvo.manifesto.read_text(encoding="utf-8")
    fm = check.parsear(texto)

    # 2 — frontmatter
    problemas, definitivos, avisos, proposta = portao_frontmatter(alvo, texto, modelo)
    rel.avisos += avisos
    rel.proposta_description = proposta
    if fm is not None:
        rel.versao = _versao(fm, alvo.tipo)
    if definitivos:
        rel.problemas = definitivos + problemas
        return rel.parar("REPROVADO", 2)
    if problemas:
        rel.problemas = problemas
        return rel.parar("PENDENTE-FRONTMATTER", 2)

    # 3 — funcionamento mínimo
    problemas, avisos, candidatos = portao_funcionamento(alvo, texto, modelo, alvo.nome, fm)
    rel.avisos += avisos
    rel.candidatos = candidatos
    if problemas:
        rel.problemas = problemas
        return rel.parar("REPROVADO", 3)

    # 4 — descrição
    motivo, erros, avisos = portao_descricao(alvo, alvo.nome, rel.versao or "", modelo)
    rel.avisos += avisos
    if motivo:
        rel.problemas = erros
        return rel.parar("PENDENTE-DESCRICAO", 4, motivo)
    return rel.parar("REVISADO", 4)


def registrar(projeto: Path, local: str):
    """Grava `reviewed` no recurso de `local`, com o escritor do `status.py` (plano 0019).

    Devolve o `ResultadoSet` do escritor. Quem chama só o faz sobre um relatório `REVISADO`.
    """
    manifesto = identificar(projeto, local).manifesto
    return _carregar_status().registrar_revisado(projeto, manifesto)


def formatar(rel: Relatorio) -> str:
    saida = [
        f"RESULTADO: {rel.resultado}",
        f"PORTAO: {rel.portao}",
        f"RECURSO: {rel.tipo}/{rel.nome}" + (f" v{rel.versao}" if rel.versao else ""),
    ]
    if rel.motivo:
        saida.append(f"MOTIVO: {rel.motivo}")
    for titulo, simbolo, itens in (
        ("PROBLEMAS", "✗", rel.problemas),
        ("AVISOS", "⚠", rel.avisos),
        ("CANDIDATOS", "?", rel.candidatos),
    ):
        if itens:
            saida.append(f"{titulo}:")
            saida += [f"  {simbolo} {item}" for item in itens]
    if rel.proposta_description:
        saida.append(f"PROPOSTA-DESCRIPTION: {rel.proposta_description}")
    return "\n".join(saida)


# ── CLI ───────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("projeto", type=Path)
    parser.add_argument("local", help="caminho do manifesto relativo ao projeto — ex.: skills/deep-research/SKILL.md")
    parser.add_argument("--templates", type=Path, default=Path(__file__).resolve().parent.parent / "templates")
    parser.add_argument(
        "--registrar",
        action="store_true",
        help="grava `reviewed` no recurso, só se o resultado é REVISADO",
    )
    args = parser.parse_args(argv)

    projeto = args.projeto.expanduser().resolve()
    if not projeto.is_dir():
        print(f"erro: projeto não encontrado — {projeto}", file=sys.stderr)
        return 2
    try:
        relatorio = revisar(projeto, args.local, args.templates.expanduser().resolve())
    except ErroUso as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(formatar(relatorio))
    if args.registrar and relatorio.resultado == "REVISADO":
        gravado = registrar(projeto, args.local)
        if not gravado.ok:
            print(f"erro: {gravado.mensagem}", file=sys.stderr)
            return 2
        print(f"REGISTRADO: {gravado.mensagem}")
    return 0 if relatorio.resultado == "REVISADO" else 1


if __name__ == "__main__":
    sys.exit(main())

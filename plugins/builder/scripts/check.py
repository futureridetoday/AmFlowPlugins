#!/usr/bin/env python3
"""Verificador de frontmatter de skill do AmFlow.

Aplica as dezessete regras verificáveis de scripts/frontmatter/skill-frontmatter.md
§5. A norma é recurso de sistema e não viaja (skill-frontmatter.md:28); este
script viaja. `vendor.py` o copia verbatim para `plugins/builder/scripts/` do
AmFlowPlugins, onde o Builder o executa — a aplicação da norma alcança o Creator
sem que o arquivo da norma saia daqui. A cópia é gerada, nunca editada do outro
lado: correção entra neste arquivo e desce por uma nova execução do vendor.

Segue fora de skill publicada — vive na raiz do plugin, não dentro de um recurso
submetido ao Hub.

O verificador assume o contexto "Fonte" (repo do Creator) da tabela de
obrigatoriedade da §3 — é o único contexto que as tarefas que o consomem
(migração das dezesseis skills, engate no CI) precisam checar. `amflow-hub-id`
e `amflow-source`, que só se aplicam a bundle publicado ou cópia instalada,
não entram na lista de obrigatórias aqui.

R-13 foi removida em 2026-08-28, com a flag --portavel que a acionava. Ela
impunha o template portável, que deixou de existir: a medição da §4 mostrou que
as extensões atravessam o upload do Cowork. O número fica vago de propósito —
regras são citadas por número em testes e relatórios, e renumerar quebraria
referência já escrita.

Uso:
  check.py <diretório-da-skill> [<diretório> ...]

Sai com 0 se todas as skills passam, 1 se alguma reprova.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── §2 — campos aceitos no topo ──────────────────────────────────────────

CAMPOS_SPEC = ("name", "description", "license", "compatibility", "allowed-tools", "metadata")
CAMPOS_EXTENSAO = (
    "when_to_use",
    "disable-model-invocation",
    "user-invocable",
    "paths",
    "context",
    "agent",
    "effort",
    "model",
    "shell",
    "arguments",
    "argument-hint",
    "disallowed-tools",
    "background",
    "hooks",
)
CAMPOS_TOPO = frozenset(CAMPOS_SPEC + CAMPOS_EXTENSAO)
CAMPOS_OBRIGATORIOS = frozenset({"name", "description", "license", "metadata"})

# §2 — tetos de tamanho da spec Agent Skills, condição de validade do arquivo.
# Nenhum era conferido até 2026-08-27.
#
# Não confundir com o teto de 1.536 do Claude Code: aquele trunca
# `description` + `when_to_use` na listagem, para poupar contexto. Um limita o
# arquivo, o outro encurta a exibição.
LIMITES_TAMANHO = {
    "name": 64,
    "description": 1024,
    "compatibility": 500,
}

# metadata e hooks são mapas — valor inline vazio é a forma correta deles
# ("chave:" seguida de linhas indentadas), não uma omissão a reprovar.
CAMPOS_MAPA = frozenset({"metadata", "hooks"})

# Valor default documentado (§2 "Nunca declarar valor default") — declarar é
# ruído mesmo não estando vazio. context/model/allowed-tools etc. já caem no
# checador de vazio genérico; estes três têm default não-vazio.
VALOR_DEFAULT = {
    "disable-model-invocation": "false",
    "user-invocable": "true",
    "shell": "bash",
}

# ── §3 — metadata ─────────────────────────────────────────────────────────

# Obrigatórias a partir do momento em que existem, na fonte (repo do
# Creator). amflow-hub-id (após a 1ª publicação) e amflow-source (não
# aplicável na fonte) ficam fora — ver docstring do módulo.
METADATA_OBRIGATORIA_FONTE = (
    "amflow-version",
    "amflow-status",
    "amflow-author",
    "amflow-author-id",
    "amflow-updated",
    "amflow-tags",
    "amflow-dependencies",
)

# Dentro das sete, só estas exigem valor não-vazio quando presentes. As duas
# de fora (tags, dependencies) exigem só a chave — medição em 2026-08-26 contra
# as dezessete skills reais (AF + AP): 16 têm dependencies vazio hoje, e não é
# defeito, é skill sem dependência. Amarrar R-07 a "não-vazio" também para
# amflow-dependencies tornaria a regra impossível de satisfazer pela maioria
# das skills existentes. amflow-tags fica de fora dessa exceção: as
# dezessete têm tag real, sem contraexemplo no disco.
METADATA_OBRIGATORIA_COM_VALOR = (
    "amflow-version",
    "amflow-status",
    "amflow-author",
    "amflow-author-id",
    "amflow-updated",
    "amflow-tags",
)

STATUS_VALIDOS = frozenset(
    {
        "draft",
        "review",
        "pending_review",
        "changes_requested",
        "rejected",
        "published",
        "suspended",
        "deprecated",
    }
)

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DEPENDENCIA_RE = re.compile(r"^[a-z][a-z0-9]*/[a-z0-9][a-z0-9-]*@\S+$")
_MODULO_RE = re.compile(r"^amflow\.module\.[a-z0-9][a-z0-9-]*$")
# Spec Agent Skills: minúsculas, números e hífen, sem hífen inicial, final nem
# consecutivo. O teto de 64 é da R-14 — esta regra cuida só da forma.
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

_LISTA_RE = re.compile(r"^\[.*\]$")
_BOOL_RE = re.compile(r"^(true|false)$")
_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")

_CHAVE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<chave>[A-Za-z][A-Za-z0-9_.-]*):\s*(?P<valor>.*?)\s*$")
_BLOCO_RE = re.compile(r"^[|>][-+]?\d*$")


@dataclass
class Campo:
    nome: str
    valor_bruto: str
    linha: int
    # Valor resolvido para medir tamanho: inline sem aspas, ou o corpo
    # desindentado quando o valor é um block scalar (`|`, `>`). As demais
    # regras seguem lendo valor_bruto — só as de tamanho precisam do corpo.
    texto: str = ""


@dataclass
class Frontmatter:
    topo: dict[str, Campo] = field(default_factory=dict)
    ordem_topo: list[str] = field(default_factory=list)
    metadata: dict[str, Campo] = field(default_factory=dict)


@dataclass
class Violacao:
    regra: str
    mensagem: str
    linha: int | None = None

    def __str__(self) -> str:
        onde = f":{self.linha}" if self.linha else ""
        return f"[{self.regra}]{onde} {self.mensagem}"


# ── parsing — deliberadamente não é um parser YAML genérico ─────────────
#
# Um parser YAML de verdade descarta comentário e não distingue "chave
# ausente" de "chave comentada" — exatamente a informação que R-04 precisa
# (campo default vira comentário no template, nunca linha ativa). O domínio
# é estreito o bastante (sem block scalar, sem alias, sem multi-documento)
# para um parser de linha bastar.


def _remover_comentario(linha: str) -> str:
    """Corta a linha no primeiro '#' fora de aspas, no início ou após espaço."""
    dentro = ""
    for i, ch in enumerate(linha):
        if dentro:
            if ch == dentro:
                dentro = ""
        elif ch in "'\"":
            dentro = ch
        elif ch == "#" and (i == 0 or linha[i - 1] in " \t"):
            return linha[:i]
    return linha


def extrair_bloco(texto: str) -> list[str] | None:
    """Linhas entre o '---' de abertura e o de fechamento — None sem os dois."""
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return None
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            return linhas[1:i]
    return None


def _corpo_do_bloco(linhas: list[str], inicio: int, indent_chave: int) -> tuple[str, int]:
    """Corpo de um block scalar e o índice da primeira linha após ele.

    Consome as linhas mais indentadas que a chave, desindenta pela menor
    indentação entre as não-vazias e devolve o texto. Comentário não é
    removido: dentro de um bloco, '#' é conteúdo.
    """
    corpo: list[str] = []
    fim = inicio + 1
    for i in range(inicio + 1, len(linhas)):
        linha = linhas[i]
        if linha.strip() and len(linha) - len(linha.lstrip()) <= indent_chave:
            break
        corpo.append(linha)
        fim = i + 1
    recuo = min(
        (len(l) - len(l.lstrip()) for l in corpo if l.strip()),
        default=0,
    )
    return "\n".join(l[recuo:] if l.strip() else "" for l in corpo).strip(), fim


def parsear(texto: str) -> Frontmatter | None:
    """Frontmatter estruturado — None quando não há bloco '---' bem-formado."""
    linhas = extrair_bloco(texto)
    if linhas is None:
        return None

    fm = Frontmatter()
    dentro_metadata = False
    pular_ate = -1
    for offset, linha_bruta in enumerate(linhas):
        if offset < pular_ate:
            continue  # corpo de block scalar, já consumido
        linha = _remover_comentario(linha_bruta)
        if not linha.strip():
            continue
        m = _CHAVE_RE.match(linha)
        if not m:
            continue
        indent = len(m.group("indent"))
        chave = m.group("chave")
        valor = m.group("valor")
        num_linha = offset + 2  # linha 1 é o '---' de abertura

        if _BLOCO_RE.match(valor):
            texto, pular_ate = _corpo_do_bloco(linhas, offset, indent)
        else:
            texto = _sem_aspas(valor).strip()

        if indent == 0:
            dentro_metadata = chave == "metadata"
            fm.topo[chave] = Campo(chave, valor, num_linha, texto)
            fm.ordem_topo.append(chave)
        elif dentro_metadata:
            fm.metadata[chave] = Campo(chave, valor, num_linha, texto)
        # indent > 0 fora de metadata (ex.: dentro de hooks:) — não governado
        # pelas dezessete regras, ignorado de propósito.

    return fm


def _tem_aspas(valor: str) -> bool:
    return len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "'\""


def _sem_aspas(valor: str) -> str:
    return valor[1:-1] if _tem_aspas(valor) else valor


def _vazio(valor: str) -> bool:
    return _sem_aspas(valor).strip() in ("", "[]", "{}")


# ── as dezessete regras (§5) ──────────────────────────────────────────────────


def r02_campos_desconhecidos(fm: Frontmatter) -> list[Violacao]:
    return [
        Violacao("R-02", f"campo fora da norma: '{chave}'", campo.linha)
        for chave, campo in fm.topo.items()
        if chave not in CAMPOS_TOPO
    ]


def r03_obrigatorios_ausentes(fm: Frontmatter) -> list[Violacao]:
    return [
        Violacao("R-03", f"campo obrigatório ausente: '{chave}'")
        for chave in CAMPOS_OBRIGATORIOS
        if chave not in fm.topo
    ]


def r04_vazio_ou_default(fm: Frontmatter) -> list[Violacao]:
    violacoes: list[Violacao] = []
    for chave, campo in fm.topo.items():
        if chave in CAMPOS_MAPA:
            continue
        if _vazio(campo.valor_bruto):
            violacoes.append(
                Violacao("R-04", f"campo '{chave}' vazio — omitir em vez de declarar vazio", campo.linha)
            )
            continue
        default = VALOR_DEFAULT.get(chave)
        if default is not None and _sem_aspas(campo.valor_bruto).strip() == default:
            violacoes.append(
                Violacao("R-04", f"campo '{chave}' no valor default ({default}) — omitir", campo.linha)
            )
    return violacoes


def r05_metadata_nao_string(fm: Frontmatter) -> list[Violacao]:
    violacoes: list[Violacao] = []
    for chave, campo in fm.metadata.items():
        v = campo.valor_bruto
        if _tem_aspas(v):
            continue
        if _LISTA_RE.match(v) or _BOOL_RE.match(v) or _NUM_RE.match(v):
            violacoes.append(Violacao("R-05", f"metadata.{chave} não é string: '{v}'", campo.linha))
    return violacoes


def r06_prefixo_amflow(fm: Frontmatter) -> list[Violacao]:
    violacoes: list[Violacao] = []
    for chave, campo in fm.metadata.items():
        if chave.startswith("amflow-") or _MODULO_RE.match(chave):
            continue
        violacoes.append(Violacao("R-06", f"metadata.{chave} sem o prefixo 'amflow-'", campo.linha))
    return violacoes


def r07_obrigatorias_do_contexto(fm: Frontmatter) -> list[Violacao]:
    violacoes: list[Violacao] = []
    for chave in METADATA_OBRIGATORIA_FONTE:
        campo = fm.metadata.get(chave)
        if campo is None:
            violacoes.append(Violacao("R-07", f"metadata.{chave} obrigatória na fonte e ausente"))
            continue
        if chave in METADATA_OBRIGATORIA_COM_VALOR and _vazio(campo.valor_bruto):
            violacoes.append(Violacao("R-07", f"metadata.{chave} obrigatória na fonte e vazia"))
    return violacoes


def r08_version_semver(fm: Frontmatter) -> list[Violacao]:
    campo = fm.metadata.get("amflow-version")
    if campo is None:
        return []
    if not _tem_aspas(campo.valor_bruto):
        return [Violacao("R-08", "amflow-version sem aspas", campo.linha)]
    if not _SEMVER_RE.match(_sem_aspas(campo.valor_bruto)):
        return [Violacao("R-08", f"amflow-version não é semver: {campo.valor_bruto}", campo.linha)]
    return []


def r09_updated_data(fm: Frontmatter) -> list[Violacao]:
    campo = fm.metadata.get("amflow-updated")
    if campo is None:
        return []
    if not _DATA_RE.match(_sem_aspas(campo.valor_bruto).strip()):
        return [Violacao("R-09", f"amflow-updated não é YYYY-MM-DD: {campo.valor_bruto}", campo.linha)]
    return []


def r10_status_valido(fm: Frontmatter) -> list[Violacao]:
    campo = fm.metadata.get("amflow-status")
    if campo is None:
        return []
    if _sem_aspas(campo.valor_bruto).strip() not in STATUS_VALIDOS:
        return [Violacao("R-10", f"amflow-status inválido: {campo.valor_bruto}", campo.linha)]
    return []


def r11_dependencias_formato(fm: Frontmatter) -> list[Violacao]:
    # amflow-tags não tem estrutura própria além de "separada por espaço" —
    # qualquer string satisfaz isso. Só amflow-dependencies tem forma a checar.
    campo = fm.metadata.get("amflow-dependencies")
    if campo is None:
        return []
    valor = _sem_aspas(campo.valor_bruto).strip()
    if not valor:
        return []
    return [
        Violacao(
            "R-11",
            f"amflow-dependencies com entrada malformada: '{entrada}' — esperado type/name@version",
            campo.linha,
        )
        for entrada in valor.split()
        if not _DEPENDENCIA_RE.match(entrada)
    ]


def r12_uuid(fm: Frontmatter) -> list[Violacao]:
    violacoes: list[Violacao] = []
    for chave in ("amflow-author-id", "amflow-hub-id"):
        campo = fm.metadata.get(chave)
        if campo is None:
            continue
        if not _UUID_RE.match(_sem_aspas(campo.valor_bruto).strip()):
            violacoes.append(Violacao("R-12", f"metadata.{chave} não é uuid: {campo.valor_bruto}", campo.linha))
    return violacoes


def r17_name_formato(fm: Frontmatter) -> list[Violacao]:
    """Forma do `name` exigida pela spec. O tamanho é da R-14."""
    campo = fm.topo.get("name")
    if campo is None:
        return []  # ausência é R-03
    valor = _sem_aspas(campo.valor_bruto).strip()
    if not valor or _NAME_RE.match(valor):
        return []
    return [
        Violacao(
            "R-17",
            f"name fora do formato da spec (minúsculas, números e hífen simples): '{valor}'",
            campo.linha,
        )
    ]


def r14_r15_r16_tamanho(fm: Frontmatter) -> list[Violacao]:
    """Os tetos da §2 — um número de regra por campo, para o relatório apontar qual."""
    regra_do_campo = {"name": "R-14", "description": "R-15", "compatibility": "R-16"}
    violacoes: list[Violacao] = []
    for chave, teto in LIMITES_TAMANHO.items():
        campo = fm.topo.get(chave)
        if campo is None:
            continue
        tamanho = len(campo.texto)
        if tamanho > teto:
            violacoes.append(
                Violacao(
                    regra_do_campo[chave],
                    f"{chave} tem {tamanho} caracteres, acima do teto de {teto}",
                    campo.linha,
                )
            )
    return violacoes


def r18_name_igual_ao_diretorio(texto: str, nome_diretorio: str) -> list[Violacao]:
    """A spec exige que `name` case com o diretório pai. Só verificável no disco."""
    fm = parsear(texto)
    if fm is None:
        return []  # sem frontmatter — é R-03
    campo = fm.topo.get("name")
    if campo is None:
        return []  # ausência é R-03
    valor = _sem_aspas(campo.valor_bruto).strip()
    if not valor or valor == nome_diretorio:
        return []
    return [
        Violacao("R-18", f"name '{valor}' diferente do diretório '{nome_diretorio}'", campo.linha)
    ]


def r01_arquivo_interno(caminho_relativo: Path, texto: str) -> Violacao | None:
    """None quando o arquivo interno está em conformidade. Nunca chamada para o SKILL.md."""
    fm = parsear(texto)
    if fm is None:
        return None  # sem frontmatter — sempre permitido
    if caminho_relativo.suffix == ".md" and set(fm.topo.keys()) == {"description"}:
        return None  # item de catálogo — o campo único (§1, só markdown)
    return Violacao("R-01", f"arquivo interno com frontmatter fora do padrão de catálogo: {caminho_relativo}")


def verificar_skill_md(texto: str) -> list[Violacao]:
    """R-02 a R-17 sobre o conteúdo de um SKILL.md."""
    fm = parsear(texto)
    if fm is None:
        return [Violacao("R-03", "frontmatter ausente ou malformado — sem '---' de abertura e fechamento")]

    violacoes: list[Violacao] = []
    violacoes += r02_campos_desconhecidos(fm)
    violacoes += r03_obrigatorios_ausentes(fm)
    violacoes += r04_vazio_ou_default(fm)
    violacoes += r05_metadata_nao_string(fm)
    violacoes += r06_prefixo_amflow(fm)
    violacoes += r07_obrigatorias_do_contexto(fm)
    violacoes += r08_version_semver(fm)
    violacoes += r09_updated_data(fm)
    violacoes += r10_status_valido(fm)
    violacoes += r11_dependencias_formato(fm)
    violacoes += r12_uuid(fm)
    violacoes += r14_r15_r16_tamanho(fm)
    violacoes += r17_name_formato(fm)
    return violacoes


def verificar_skill(diretorio: Path) -> dict[str, list[Violacao]]:
    """Um relatório por arquivo reprovado — SKILL.md (R-02 a R-18) e arquivo interno (R-01)."""
    skill_md = diretorio / "SKILL.md"
    if not skill_md.is_file():
        return {"SKILL.md": [Violacao("R-03", "SKILL.md não encontrado no diretório")]}

    relatorio: dict[str, list[Violacao]] = {}

    texto_skill = skill_md.read_text(encoding="utf-8")
    violacoes_skill = verificar_skill_md(texto_skill)
    violacoes_skill += r18_name_igual_ao_diretorio(texto_skill, diretorio.name)
    if violacoes_skill:
        relatorio["SKILL.md"] = violacoes_skill

    for caminho in sorted(diretorio.rglob("*")):
        if not caminho.is_file() or caminho == skill_md:
            continue
        try:
            texto = caminho.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relativo = caminho.relative_to(diretorio)
        violacao = r01_arquivo_interno(relativo, texto)
        if violacao is not None:
            relatorio[str(relativo)] = [violacao]

    return relatorio


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("diretorios", nargs="+", type=Path, help="diretório da skill (contém SKILL.md)")
    args = parser.parse_args(argv)

    algum_reprovado = False
    for diretorio in args.diretorios:
        nome = diretorio.name
        if not diretorio.is_dir():
            print(f"FALHA  {nome}: diretório não encontrado — {diretorio}")
            algum_reprovado = True
            continue

        relatorio = verificar_skill(diretorio)
        if not relatorio:
            print(f"OK     {nome}")
            continue

        algum_reprovado = True
        print(f"FALHA  {nome}")
        for arquivo, violacoes in relatorio.items():
            for v in violacoes:
                print(f"  {arquivo}: {v}")

    return 1 if algum_reprovado else 0


if __name__ == "__main__":
    sys.exit(main())

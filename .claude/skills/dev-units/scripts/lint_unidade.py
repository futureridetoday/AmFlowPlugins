#!/usr/bin/env python3
"""Gate de entrada do modo `implement` — unidade 0002-06.

Recusa começar uma unidade que não sobrevive ao cold-start e devolve a lista
do que falta, para a correção voltar ao `derive` em vez de ser descoberta
pelo executor no meio do trabalho.

Três decisões da norma moldam o comportamento: teste **declarado**, não
existente (decisão 15) — o campo `test` precisa estar presente, o arquivo que
ele aponta não; teto de **8 passos** na Sequência (decisão 1), acima disso a
unidade divide; e `unit_type` restrito a `dev` ou `plan` (decisão 28).

O gate verifica presença e forma, não coerência entre Contrato e Sequência —
isso é julgamento, fora do alcance de regex. Ver a nota correspondente em
docs/plan/builder/0002-dev-units/06-lint-unidade.md.
"""

from __future__ import annotations

import re
from pathlib import Path

import regioes

CAMPOS_FRONTMATTER = ("unit_id", "unit_type", "core", "module", "state", "test")

BLOCOS_CORPO = (
    "Contrato",
    "Sequência",
    "Arquivos",
    "Dependências",
    "Normas aplicáveis",
    "Critério de aceite",
    "Verificação",
)

TETO_PASSOS = 8
UNIT_TYPES_VALIDOS = ("dev", "plan")

_UNIT_ID_RE = re.compile(r"^\d{4}-\d{2}$")
_PASSO_RE = re.compile(r"(?m)^\d+\.\s")
_CAMINHO_RE = re.compile(r"`[^`]*/[^`]*`")


def lint(unidade: Path) -> list[str]:
    """Verifica se `unidade` sobrevive ao cold-start — lista vazia quando aprovada."""
    texto = unidade.read_text(encoding="utf-8")
    corpo = _corpo(texto)

    problemas: list[str] = []
    problemas.extend(_checar_frontmatter(unidade))
    problemas.extend(_checar_blocos(corpo))
    problemas.extend(_checar_sequencia(corpo))
    problemas.extend(_checar_criterio_aceite(corpo))
    problemas.extend(_checar_arquivos(corpo))
    return problemas


def _corpo(texto: str) -> str:
    """Conteúdo após o frontmatter — o texto inteiro se não houver '---' de abertura."""
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return texto
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            return "\n".join(linhas[i + 1 :])
    return ""


def _checar_frontmatter(unidade: Path) -> list[str]:
    """Exige os campos do cold-start; formato de `unit_id`/`unit_type` só quando declarados."""
    try:
        valores = {
            chave: regioes.ler_campo(unidade, chave) for chave in CAMPOS_FRONTMATTER
        }
    except ValueError:
        return ["frontmatter ausente ou malformado — sem '---' de abertura e fechamento"]

    problemas = [
        f"campo obrigatório ausente no frontmatter: {chave}"
        for chave, valor in valores.items()
        if not (valor and valor.strip())
    ]

    unit_id = valores.get("unit_id")
    if unit_id and unit_id.strip() and not _UNIT_ID_RE.match(unit_id.strip()):
        problemas.append(f"unit_id fora do formato NNNN-NN: {unit_id!r}")

    unit_type = valores.get("unit_type")
    if unit_type and unit_type.strip() and unit_type.strip() not in UNIT_TYPES_VALIDOS:
        problemas.append(f"unit_type inválido, esperado 'dev' ou 'plan': {unit_type!r}")

    return problemas


def _checar_blocos(corpo: str) -> list[str]:
    """Exige a presença de cada bloco — Responsabilidade é texto em negrito, os demais são headings."""
    problemas = []
    if not re.search(r"(?m)^\*\*Responsabilidade:\*\*", corpo):
        problemas.append("bloco ausente: Responsabilidade")

    for bloco in BLOCOS_CORPO:
        if not re.search(rf"(?m)^##\s+{re.escape(bloco)}\s*$", corpo):
            problemas.append(f"bloco ausente: {bloco}")

    return problemas


def _secao(corpo: str, nome: str) -> str | None:
    """Conteúdo de `## nome` até o próximo heading `## ` ou o fim do corpo — None se ausente."""
    padrao = re.compile(rf"(?ms)^##\s+{re.escape(nome)}\s*$\n(.*?)(?=^##\s+|\Z)")
    m = padrao.search(corpo)
    return m.group(1) if m else None


def _checar_sequencia(corpo: str) -> list[str]:
    """Ausente já é reportada por `_checar_blocos`; aqui cobre vazia e acima do teto."""
    secao = _secao(corpo, "Sequência")
    if secao is None:
        return []

    passos = _PASSO_RE.findall(secao)
    if not passos:
        return ["Sequência sem passos numerados"]
    if len(passos) > TETO_PASSOS:
        return [f"Sequência com {len(passos)} passos, acima do teto de {TETO_PASSOS}"]
    return []


def _checar_criterio_aceite(corpo: str) -> list[str]:
    """Exige ao menos uma frase — não só o cabeçalho."""
    secao = _secao(corpo, "Critério de aceite")
    if secao is None:
        return []
    if not secao.strip():
        return ["Critério de aceite sem conteúdo"]
    return []


def _checar_arquivos(corpo: str) -> list[str]:
    """Exige ao menos um caminho concreto (crase com '/') na tabela de Arquivos."""
    secao = _secao(corpo, "Arquivos")
    if secao is None:
        return []
    if not _CAMINHO_RE.search(secao):
        return ["tabela de Arquivos sem caminho concreto"]
    return []

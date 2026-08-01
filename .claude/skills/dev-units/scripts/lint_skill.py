#!/usr/bin/env python3
"""Lint de completude estrutural de um SKILL.md — unidade 0002-10.

Dá oráculo determinístico às cinco unidades da Fase 2 (11-15), que entregam
markdown, não código. Verifica só o que é objetivamente verificável: os 21
campos de frontmatter que as 11 skills do repositório já compartilham
(decisão D-02, não a tabela de recurso publicável do CLAUDE.md, que inclui
author_id e price), presença de modo pedido no corpo, e existência/permissão
dos caminhos citados. Não verifica se a skill funciona bem — distinção
deliberada, ver docs/plan/builder/0002-dev-units/10-lint-skill.md.

O passo 6 ignora bloco de código e code span ao varrer link relativo — mesma
lição do scripts/move-md.py: documentação normativa cita caminho como
exemplo, e tratá-lo como link real produz falso positivo.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import lib
import regioes

# O conjunto presente em 11 de 11 skills do repositório (decisão D-02) — não
# a tabela de recurso publicável do CLAUDE.md, que inclui author_id e price
# e não é o que as skills reais declaram.
CAMPOS_FRONTMATTER = (
    "name",
    "description",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "effort",
    "context",
    "shell",
    "type",
    "project",
    "author",
    "created",
    "status",
    "version",
    "updated",
    "scope",
    "auto_load",
    "tags",
    "dependencies",
    "hub_id",
    "source",
)

# Interpretadores que dispensam bit de execução no script citado.
_INTERPRETES_RE = re.compile(r"\b(python3|python|bash|sh|zsh|node|npx)\b")

# Abertura/fechamento de bloco de código — mesma marca do move-md.py.
_FENCE_RE = re.compile(r"^\s*(```|~~~)")

# [texto](destino) — mesma captura do move-md.py.
_LINK_RE = re.compile(r"(?<=\]\()([^)\s]+)(?=\))")


def lint(skill: Path, modos: list[str] | None = None) -> list[str]:
    """Verifica a completude estrutural de `skill` — lista vazia quando aprovada.

    Levanta `FileNotFoundError` se o arquivo não existe. Frontmatter ausente
    ou malformado entra na lista devolvida, não é exceção.
    """
    texto = skill.read_text(encoding="utf-8")
    corpo = _corpo(texto)

    problemas: list[str] = []
    problemas.extend(_checar_frontmatter(skill))
    problemas.extend(_checar_nome_e_descricao(skill))
    problemas.extend(_checar_modos(corpo, modos or []))
    problemas.extend(_checar_scripts(skill, corpo))
    problemas.extend(_checar_links(skill, corpo))
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


def _checar_frontmatter(skill: Path) -> list[str]:
    """Exige a presença dos 21 campos — vazio ou não é o passo 2, não este."""
    try:
        valores = {chave: regioes.ler_campo(skill, chave) for chave in CAMPOS_FRONTMATTER}
    except ValueError:
        return ["frontmatter ausente ou malformado — sem '---' de abertura e fechamento"]

    return [
        f"campo obrigatório ausente no frontmatter: {chave}"
        for chave, valor in valores.items()
        if valor is None
    ]


def _checar_nome_e_descricao(skill: Path) -> list[str]:
    """`name` e `description` não vazios, e `name` igual ao diretório da skill."""
    try:
        nome = regioes.ler_campo(skill, "name")
        descricao = regioes.ler_campo(skill, "description")
    except ValueError:
        return []

    problemas = []
    if not (nome and nome.strip()):
        problemas.append("campo 'name' vazio")
    elif nome.strip() != skill.parent.name:
        problemas.append(
            f"'name' ({nome.strip()!r}) não corresponde ao diretório da skill ({skill.parent.name!r})"
        )

    if not (descricao and descricao.strip()):
        problemas.append("campo 'description' vazio")

    return problemas


def _checar_modos(corpo: str, modos: list[str]) -> list[str]:
    """Cada modo pedido precisa aparecer citado em algum lugar do corpo."""
    return [f"modo não declarado no corpo: {modo}" for modo in modos if modo not in corpo]


def _caminhos_de_scripts(skill: Path, corpo: str) -> dict[str, list[str]]:
    """Caminhos citados sob o `scripts/` da própria skill, com o texto que precede cada um na linha.

    Só conta o prefixo inequívoco `.claude/skills/<nome>/scripts/` — uma
    citação nua como `scripts/x.py`, ou `./scripts/x.py`, é ambígua: pode ser
    de outro diretório de trabalho (o `cd hub` que precede
    `./scripts/new-migration.sh` em hub-env/SKILL.md aponta para
    `hub/scripts/`, não para o `scripts/` da própria skill nem o da raiz do
    repositório) e não é checável sem interpretar o shell ao redor.
    """
    nome = skill.parent.name
    padrao = re.compile(r"\.claude/skills/" + re.escape(nome) + r"/scripts/[^\s`)\"'<>]+")

    encontrados: dict[str, list[str]] = {}
    for linha in corpo.split("\n"):
        for m in padrao.finditer(linha):
            prefixo = linha[: m.start()]
            encontrados.setdefault(m.group(0), []).append(prefixo)
    return encontrados


def _checar_scripts(skill: Path, corpo: str) -> list[str]:
    """Existência em disco (passo 4) e bit de execução ou interpretador explícito (passo 5)."""
    raiz = lib.repo_root()
    problemas: list[str] = []
    for caminho, prefixos in _caminhos_de_scripts(skill, corpo).items():
        alvo = raiz / caminho
        if not alvo.is_file():
            problemas.append(f"script citado não existe: {caminho}")
            continue

        executavel = os.access(alvo, os.X_OK)
        interpretado = any(_INTERPRETES_RE.search(prefixo) for prefixo in prefixos)
        if not executavel and not interpretado:
            problemas.append(
                f"script sem bit de execução e sem interpretador explícito: {caminho}"
            )
    return problemas


def _links_do_corpo(corpo: str) -> list[str]:
    """Destinos de `[texto](destino)` fora de bloco de código e de code span.

    Mesma lógica do scripts/move-md.py: bloco delimitado por crase ou til
    tripla é pulado inteiro, e dentro de uma linha só os trechos de índice
    par (fora de crase simples) são varridos.
    """
    destinos: list[str] = []
    dentro_de_bloco = False
    for linha in corpo.split("\n"):
        if _FENCE_RE.match(linha):
            dentro_de_bloco = not dentro_de_bloco
            continue
        if dentro_de_bloco:
            continue
        partes = linha.split("`")
        for i in range(0, len(partes), 2):
            destinos.extend(_LINK_RE.findall(partes[i]))
    return destinos


def _e_relativo(destino: str) -> bool:
    """URL, âncora da própria página e caminho absoluto não dependem de onde a skill vive."""
    if not destino or destino.startswith(("#", "/", "http://", "https://", "mailto:")):
        return False
    return "://" not in destino


def _checar_links(skill: Path, corpo: str) -> list[str]:
    """Cada link relativo precisa resolver a partir do diretório da própria skill."""
    problemas = []
    for destino in _links_do_corpo(corpo):
        if not _e_relativo(destino):
            continue
        caminho = destino.split("#", 1)[0]
        alvo = (skill.parent / caminho).resolve()
        if not alvo.exists():
            problemas.append(f"link não resolve: {destino}")
    return problemas

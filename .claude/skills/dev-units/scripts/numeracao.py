#!/usr/bin/env python3
"""Numeração de plano e de unidade — unidade 0002-04.

Fonte única do próximo número: o plano recebe quatro dígitos sequenciais
globais, lidos de `_planos.md`; a unidade recebe dois dígitos que recomeçam
a cada plano, lidos do disco. Sem isso, dois planos aprovados na mesma
semana colidiriam (norma, decisões 22 e 23).

Por que ler a região e não o arquivo inteiro: fora dos marcadores há prosa
que cita número como exemplo — "0003-02" aparece no próprio `_planos.md`, no
texto sobre a coluna `Origem`. Ler o arquivo inteiro capturaria esse número e
saltaria a numeração — por isso `proximo_plano` nunca lê além da região
`planos` devolvida por `regioes.ler_regiao`.

Por que o disco decide a unidade, e não o backlog: o backlog é projeção — se
estiver desatualizado, o disco continua correto, e a norma manda projetar o
que já existe nele. `proxima_unidade` por isso lista o diretório do plano em
vez de ler o backlog.
"""

from __future__ import annotations

import re
from pathlib import Path

import lib
import regioes

LARGURA_PLANO = 4
LARGURA_UNIDADE = 2

PADRAO_PRIMEIRA_COLUNA = re.compile(r"^\|\s*(\d+)\s*\|")
PADRAO_ARQUIVO_UNIDADE = re.compile(r"^(\d{2})-.+\.md$")


def _numeros_de_planos(miolo: str) -> list[int]:
    """Números da primeira coluna de cada linha de dado — cabeçalho e separador não têm dígito ali."""
    numeros = []
    for linha in miolo.splitlines():
        m = PADRAO_PRIMEIRA_COLUNA.match(linha.strip())
        if m:
            numeros.append(int(m.group(1)))
    return numeros


def proximo_plano() -> str:
    """Próximo número de plano — quatro dígitos, sequencial global.

    Lê só a região `planos` de `_planos.md` (norma, decisão 24). Tabela
    vazia começa em `"0001"`. Levanta `RuntimeError` em vez de truncar em
    silêncio se o próximo número não couber em quatro dígitos.
    """
    caminho = lib.planos_md()
    miolo = regioes.ler_regiao(caminho, "planos")
    if miolo is None:
        raise ValueError(f"região 'planos' ausente em {caminho}")

    numeros = _numeros_de_planos(miolo)
    proximo = max(numeros) + 1 if numeros else 1

    limite = 10**LARGURA_PLANO - 1
    if proximo > limite:
        raise RuntimeError(
            f"número de plano estourou {LARGURA_PLANO} dígitos — {proximo} > {limite}"
        )
    return str(proximo).zfill(LARGURA_PLANO)


def proxima_unidade(dir_plano: Path) -> str:
    """Próximo número de unidade dentro de um plano — dois dígitos, recomeça em `"01"` a cada plano.

    Lista `NN-*.md` no diretório do plano, ignorando o arquivo do próprio
    plano. Levanta `RuntimeError` em vez de truncar em silêncio se o
    próximo número não couber em dois dígitos.
    """
    arquivo_do_plano = f"{dir_plano.name}.md"

    numeros = []
    for item in dir_plano.iterdir():
        if not item.is_file() or item.name == arquivo_do_plano:
            continue
        m = PADRAO_ARQUIVO_UNIDADE.match(item.name)
        if m:
            numeros.append(int(m.group(1)))

    proximo = max(numeros) + 1 if numeros else 1

    limite = 10**LARGURA_UNIDADE - 1
    if proximo > limite:
        raise RuntimeError(
            f"número de unidade estourou {LARGURA_UNIDADE} dígitos — {proximo} > {limite}"
        )
    return str(proximo).zfill(LARGURA_UNIDADE)

#!/usr/bin/env python3
"""Oráculo de verificação — projeta `state` e `verified_at`, unidade 0002-08.

Lê o teste que a unidade declara no frontmatter, roda pelo runner da
extensão e escreve o estado derivado de volta — nunca o corpo (decisão 13).
Teste declarado mas inexistente no disco não é erro: é o caso normal de
unidade nova, e resulta em `spec` (decisão 15).

A escolha do runner compõe o que já existe em vez de reimplementar:
`scripts/test-python.sh` só aceita diretório, não arquivo — por isso o
caminho de um teste `.py` é reduzido ao diretório-pacote (o pai de `tests/`,
quando é esse o nome do pai), o mesmo valor que o próprio script já declara
em `TEST_DIRS`. Consequência: a granularidade real é de pacote, não de
arquivo — a mesma imprecisão aceita pela norma (lacuna L-05 do plano).
`.ts` roda por `npx vitest run`, com cwd em `hub/` e caminho relativo a
ele — a forma documentada em docs/plan/hub/0001-mcp/01-handler-auth.md.

Timeout conta como falha (`spec`), nunca como exceção: o objetivo do timeout
é só impedir que um teste interativo trave a verificação, não distinguir
esse caso de qualquer outro jeito de o teste não provar que passa.
"""

from __future__ import annotations

import os
import subprocess
from datetime import date
from pathlib import Path

import lib
import regioes

# Generoso o bastante para uma suíte real (inclui o cold start do vitest);
# existe só para não travar em teste interativo, não é orçamento de performance.
TIMEOUT_SEGUNDOS = 120

# Sentinela contra reentrância. Esta unidade é a única do plano capaz de se
# auto-invocar: verificar() reduz o teste ao pacote e roda a suíte inteira, e o
# teste desta unidade vive nessa suíte. Uma chamada real lá dentro reentra sem
# fim — aconteceu em 2026-07-25 e produziu 763 processos órfãos, porque
# subprocess.kill() mata só o filho direto e o timeout não alcança a árvore.
# O ambiente do subprocesso carrega a marca; reentrar levanta em vez de rodar.
SENTINELA_REENTRANCIA = "AMFLOW_VERIFICACAO_EM_CURSO"


def verificar(unidade: Path, dry_run: bool = False) -> tuple[str, bool]:
    """Deriva o estado de `unidade` a partir do teste que ela declara.

    Levanta `ValueError` se o frontmatter não declara `test`. Em `dry_run`,
    roda o teste e devolve o estado sem escrever nada — o segundo valor da
    tupla é sempre `False` nesse caso.
    """
    test_declarado = regioes.ler_campo(unidade, "test")
    if not test_declarado or not test_declarado.strip():
        raise ValueError(f"unidade não declara 'test' — {unidade}")

    raiz = lib.repo_root()
    caminho_teste = (raiz / test_declarado.strip()).resolve()

    if caminho_teste.is_file():
        estado = "verified" if _executar(caminho_teste, raiz) == 0 else "spec"
    else:
        estado = "spec"

    if dry_run:
        return estado, False

    verified_at = date.today().isoformat() if estado == "verified" else '""'
    escreveu = regioes.escrever_campos(
        unidade, {"state": estado, "verified_at": verified_at}
    )
    return estado, escreveu


def _executar(caminho_teste: Path, raiz: Path) -> int:
    """Código de saída do teste — timeout devolve falha, nunca propaga exceção.

    Recusa executar se já houver verificação em curso: é aqui que a recursão
    nasceria, e não em `verificar()`. A distinção importa — checar antes faria
    todo teste que chama `verificar()` com subprocesso mockado quebrar quando a
    própria suíte roda dentro de uma verificação, e a unidade jamais poderia
    ser promovida.
    """
    if os.environ.get(SENTINELA_REENTRANCIA):
        raise RuntimeError(
            f"execução de teste aninhada recusada — {caminho_teste}. Já há uma "
            "verificação em curso, e reentrar na suíte recursa sem que timeout "
            "ou kill contenham a árvore. Em teste, mocke subprocess.run."
        )

    comando, cwd = _comando(caminho_teste, raiz)
    ambiente = {**os.environ, SENTINELA_REENTRANCIA: "1"}
    try:
        resultado = subprocess.run(
            comando,
            cwd=cwd,
            timeout=TIMEOUT_SEGUNDOS,
            capture_output=True,
            env=ambiente,
        )
    except subprocess.TimeoutExpired:
        return 1
    return resultado.returncode


def _comando(caminho_teste: Path, raiz: Path) -> tuple[list[str], Path]:
    """Runner pela extensão do teste — `ValueError` se não for `.py` nem `.ts`."""
    if caminho_teste.suffix == ".py":
        return _comando_python(caminho_teste, raiz)
    if caminho_teste.suffix == ".ts":
        return _comando_typescript(caminho_teste, raiz)
    raise ValueError(f"extensão de teste sem runner declarado — {caminho_teste}")


def _comando_python(caminho_teste: Path, raiz: Path) -> tuple[list[str], Path]:
    """`scripts/test-python.sh <pacote>` — pacote é o pai de `tests/`, nunca o arquivo."""
    pacote = caminho_teste.parent
    if pacote.name == "tests":
        pacote = pacote.parent
    comando = [str(raiz / "scripts" / "test-python.sh"), str(pacote.relative_to(raiz))]
    return comando, raiz


def _comando_typescript(caminho_teste: Path, raiz: Path) -> tuple[list[str], Path]:
    """`npx vitest run <caminho>` a partir de `hub/` — forma documentada na unidade 0001-01."""
    hub_dir = raiz / "hub"
    comando = ["npx", "vitest", "run", str(caminho_teste.relative_to(hub_dir))]
    return comando, hub_dir

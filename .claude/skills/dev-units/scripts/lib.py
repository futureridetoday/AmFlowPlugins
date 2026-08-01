#!/usr/bin/env python3
"""Módulo comum dos scripts da skill dev-units.

Dá aos demais scripts uma origem confiável — a raiz do repositório e os caminhos
canônicos sob `docs/plan/` — sem depender de variável de ambiente nem do
diretório de trabalho de quem invoca. É módulo importado, não script executável.

`CLAUDE_PLUGIN_ROOT` não serve: o estudo mediu a variável vazia nos dois
ambientes, e no browser isso causou falha até o script ser localizado com `find`.
Auto-localização por `__file__` é o padrão que o estudo recomenda — ver
docs/plan/system/estudo-runtime-e-dependencias.md §5.3.

Todo caminho devolvido é resolvido. `relpath` entre um caminho resolvido e outro
não-resolvido produz lixo quando há symlink no meio, e no macOS `/tmp` e `/var`
são symlinks — foi exatamente assim que o move-md quebrou.
"""

from __future__ import annotations

from pathlib import Path

# Marcas da raiz. Só `.claude/` não bastaria: qualquer projeto pode ter uma.
ROOT_MARKERS = (".claude", "docs")


def _find_repo_root(start: Path) -> Path:
    """Sobe a partir de `start` até o diretório que contém todas as marcas."""
    for candidate in (start, *start.parents):
        if all((candidate / marker).is_dir() for marker in ROOT_MARKERS):
            return candidate

    marcas = " e ".join(f"{marker}/" for marker in ROOT_MARKERS)
    raise RuntimeError(
        f"raiz do repositório não localizada a partir de {start} — "
        f"nenhum diretório acima contém {marcas}. "
        "Este módulo precisa estar dentro de um clone do AmFlow."
    )


def repo_root() -> Path:
    """Raiz do AmFlow, achada a partir deste arquivo — nunca do cwd."""
    return _find_repo_root(Path(__file__).resolve().parent)


def plan_root() -> Path:
    """`docs/plan/` — onde vivem planos, unidades e normativa."""
    return (repo_root() / "docs" / "plan").resolve()


def planos_md() -> Path:
    """`_planos.md` — tabela dos planos aprovados, fonte da numeração."""
    return (plan_root() / "_planos.md").resolve()


def inbox() -> Path:
    """`_inbox/` — planos aguardando revisão e aprovação."""
    return (plan_root() / "_inbox").resolve()


def core_dir(core: str) -> Path:
    """Diretório de um core sob `docs/plan/` — hub, worker, builder, security."""
    if not core.strip():
        raise ValueError("nome de core vazio")
    if "/" in core or "\\" in core:
        raise ValueError(
            f"nome de core não pode conter separador de caminho — {core!r}"
        )
    return (plan_root() / core).resolve()

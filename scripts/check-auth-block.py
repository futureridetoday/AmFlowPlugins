#!/usr/bin/env python3
"""Guarda que toda skill-comando do Worker carrega a autenticação idêntica à fonte.

A fonte é `plugins/worker/auth/auth-check.md`. Cada skill que adota a autenticação
traz uma cópia literal entre os marcadores `<!-- auth-check:start ... -->` e
`<!-- auth-check:end -->`. A cópia existe porque o Claude Code não deixa a skill
ler arquivo fora dos diretórios de trabalho do usuário sem pedir permissão — nem
por Read, nem por injeção `!cat` — e o conteúdo do `SKILL.md` é o único que chega
sem pedido. Este guard impede a cópia de divergir da fonte.

Uso: ./scripts/check-auth-block.py
Sai com 0 se toda cópia bate com a fonte, 1 se alguma diverge ou está mal marcada.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "plugins/worker/auth/auth-check.md"
SKILLS = RAIZ / "plugins/worker/skills"

INICIO = re.compile(r"^<!-- auth-check:start\b.*-->$", re.M)
FIM = re.compile(r"^<!-- auth-check:end -->$", re.M)


def bloco(texto: str) -> str | None:
    """Conteúdo entre os marcadores, ou None se a skill não adota a autenticação."""
    inicios = list(INICIO.finditer(texto))
    fins = list(FIM.finditer(texto))
    if not inicios and not fins:
        return None
    if len(inicios) != 1 or len(fins) != 1 or fins[0].start() < inicios[0].end():
        raise ValueError("marcadores auth-check desbalanceados")
    return texto[inicios[0].end():fins[0].start()].strip("\n")


def verificar(fonte: Path, skills: Path) -> list[str]:
    esperado = fonte.read_text(encoding="utf-8").strip("\n")
    erros: list[str] = []
    for skill in sorted(skills.glob("*/SKILL.md")):
        rel = skill.relative_to(RAIZ) if skill.is_relative_to(RAIZ) else skill
        try:
            copia = bloco(skill.read_text(encoding="utf-8"))
        except ValueError as e:
            erros.append(f"{rel}: {e}")
            continue
        if copia is not None and copia != esperado:
            erros.append(f"{rel}: bloco auth-check difere de {FONTE.relative_to(RAIZ)}")
    return erros


def main() -> int:
    erros = verificar(FONTE, SKILLS)
    if erros:
        print(f"check-auth-block: {len(erros)} problema(s):\n", file=sys.stderr)
        for erro in erros:
            print(f"  - {erro}", file=sys.stderr)
        return 1
    print("check-auth-block: toda cópia bate com a fonte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

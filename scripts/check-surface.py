#!/usr/bin/env python3
"""Guarda as cinco propriedades da separação de superfícies MCP — unidade 0004-04.

As unidades 01 a 03 do plano `hub/0004-close-surface-split` (repo AmFlow)
estabeleceram que cada plugin fala com a própria superfície: chave de
servidor, host, caminho e prosa que só cita tool alcançável dali.
`.github/workflows/plugins.yml` validava só JSON e frontmatter — nada
impedia essas quatro coisas de regredir. Este guard fecha o F4 daquele
plano.

A quinta propriedade veio depois, da revisão do `new-project` em 2026-08-31:
a prosa também *nomeia* o conector, e isso não era verificado por ninguém.
Oito arquivos mandavam autorizar um conector `amflow` que não existe em
lugar nenhum — quem caísse na mensagem procuraria esse nome na lista do
`/mcp` e não acharia. As propriedades (1) e (2) já exigiam a chave certa no
JSON; a (5) passa a exigir a mesma chave na prosa que fala dela.

As duas listas de tools por superfície são copiadas de
`hub/test/api/mcp-builder.test.ts:14` e `:20`, no repositório AmFlow — este
script não alcança aquele arquivo em CI, porque vive noutro repositório
(mesmo contorno da `L-04` do plano `0001-mcp`). Se a superfície de uma tool
mudar lá, alguém precisa atualizar aqui à mão.

Uso: ./scripts/check-surface.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

RAIZ = Path(__file__).resolve().parent.parent

HOST_ESPERADO = "amflow.work"
DIRS_PROSA = ("commands", "skills", "agents")

SUPERFICIES = {
    "worker": {
        "dir": "plugins/worker",
        "chave_servidor": "amflow-worker",
        "caminho_mcp": "/mcp",
        "tools": {"search_catalog", "list_active_licenses", "check_updates", "install", "update"},
    },
    "builder": {
        "dir": "plugins/builder",
        "chave_servidor": "amflow-builder",
        "caminho_mcp": "/mcp-builder",
        "tools": {"get_resource", "me", "submission_status", "publish"},
    },
}

# Casa só a forma que a prosa do repositório usa: `tool `<nome>`` e
# `tools `<a>` e `<b>``. Nunca substring solta — é o que evita falso
# positivo em `update` dentro de `check_updates` e em nome de command como
# `/amflow-worker:install`.
NOME = r"[A-Za-z_][A-Za-z0-9_]*"
CHAVE = r"[A-Za-z][A-Za-z0-9_-]*"

# Propriedade (5): a prosa nomeia o conector nestas duas formas, e só nelas.
# Nome de command (`/amflow-worker:get`) e host não entram — não são citação
# de conector, e casá-los daria falso positivo em prosa legítima.
CITACAO_CONECTOR = re.compile(rf"\b(?:conector|servidor)(?: MCP)? `({CHAVE})`")
CITACAO_UMA = re.compile(rf"\btool `({NOME})")
CITACAO_DUAS = re.compile(rf"\btools `({NOME})[^`]*` e `({NOME})")


def citacoes_em(texto: str) -> list[str]:
    """Nomes de tool citados no texto, na forma que a prosa do repositório usa."""
    nomes = [m.group(1) for m in CITACAO_UMA.finditer(texto)]
    for m in CITACAO_DUAS.finditer(texto):
        nomes.append(m.group(1))
        nomes.append(m.group(2))
    return nomes


def verificar_declaracao(nome: str, cfg: dict, erros: list[str]) -> None:
    """Propriedades (1), (2) e (3): chave do servidor, host e caminho."""
    mcp = json.loads((RAIZ / cfg["dir"] / ".mcp.json").read_text(encoding="utf-8"))
    plugin = json.loads(
        (RAIZ / cfg["dir"] / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    chave = cfg["chave_servidor"]
    servidores = mcp.get("mcpServers", {})

    if list(servidores.keys()) != [chave]:
        erros.append(
            f"{nome}: .mcp.json declara {list(servidores.keys())}, esperado só ['{chave}']"
        )

    if plugin.get("name") != chave:
        erros.append(
            f"{nome}: plugin.json tem name={plugin.get('name')!r}, esperado {chave!r} — "
            "precisa bater com a chave em .mcp.json"
        )

    if chave in servidores:
        url = servidores[chave]["url"]
        partes = urlsplit(url)
        if partes.hostname != HOST_ESPERADO:
            erros.append(f"{nome}: host é {partes.hostname!r}, esperado {HOST_ESPERADO!r} — url={url!r}")
        if partes.path != cfg["caminho_mcp"]:
            erros.append(
                f"{nome}: caminho é {partes.path!r}, esperado {cfg['caminho_mcp']!r} — url={url!r}"
            )


def verificar_prosa(nome: str, cfg: dict, tool_por_superficie: dict[str, str], erros: list[str]) -> None:
    """Propriedade (4): nenhuma citação de tool atravessa a fronteira da superfície."""
    base = RAIZ / cfg["dir"]
    for subdir in DIRS_PROSA:
        pasta = base / subdir
        if not pasta.is_dir():
            continue
        for arquivo in sorted(pasta.rglob("*.md")):
            texto = arquivo.read_text(encoding="utf-8")
            for tool in citacoes_em(texto):
                dona = tool_por_superficie.get(tool)
                if dona is None or dona == nome:
                    continue
                rel = arquivo.relative_to(RAIZ)
                erros.append(
                    f"{rel}: cita `{tool}`, que só existe na superfície '{dona}' — "
                    f"fora do alcance do plugin '{nome}'"
                )


def verificar_conector_na_prosa(nome: str, cfg: dict, chaves: set[str], erros: list[str]) -> None:
    """Propriedade (5): a prosa nomeia o conector da própria superfície, e com a chave que existe.

    Duas falhas distintas, e a segunda é a que passou despercebida por meses:
    citar a chave da outra superfície, e citar um nome que não é chave de
    superfície nenhuma — `amflow` em vez de `amflow-builder`. O usuário não
    tem como saber que o nome está errado; ele só não encontra o conector.
    """
    base = RAIZ / cfg["dir"]
    chave = cfg["chave_servidor"]
    for subdir in DIRS_PROSA:
        pasta = base / subdir
        if not pasta.is_dir():
            continue
        for arquivo in sorted(pasta.rglob("*.md")):
            texto = arquivo.read_text(encoding="utf-8")
            for citada in {m.group(1) for m in CITACAO_CONECTOR.finditer(texto)}:
                if citada == chave:
                    continue
                rel = arquivo.relative_to(RAIZ)
                if citada in chaves:
                    erros.append(
                        f"{rel}: nomeia o conector `{citada}`, da outra superfície — "
                        f"o plugin '{nome}' fala com `{chave}`"
                    )
                else:
                    erros.append(
                        f"{rel}: nomeia o conector `{citada}`, que não é chave de servidor "
                        f"em nenhum .mcp.json — esperado `{chave}`"
                    )


def main() -> int:
    erros: list[str] = []

    for nome, cfg in SUPERFICIES.items():
        verificar_declaracao(nome, cfg, erros)

    tool_por_superficie = {
        tool: nome for nome, cfg in SUPERFICIES.items() for tool in cfg["tools"]
    }
    for nome, cfg in SUPERFICIES.items():
        verificar_prosa(nome, cfg, tool_por_superficie, erros)

    chaves = {cfg["chave_servidor"] for cfg in SUPERFICIES.values()}
    for nome, cfg in SUPERFICIES.items():
        verificar_conector_na_prosa(nome, cfg, chaves, erros)

    if erros:
        print(f"check-surface: {len(erros)} problema(s):\n", file=sys.stderr)
        for erro in erros:
            print(f"  - {erro}", file=sys.stderr)
        return 1

    print("check-surface: as cinco propriedades valem para os dois plugins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

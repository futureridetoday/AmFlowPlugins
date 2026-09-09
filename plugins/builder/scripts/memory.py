#!/usr/bin/env python3
"""Lógica determinística do comando `memory` do plugin Builder.

Especificação: docs/plan/builder/0008-user-memory/index.md (§1 a §3), no repo
AmFlow. Este script é chamado pela tool Bash a partir de
`plugins/builder/commands/memory.md` como
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py --stdin <<'AMFLOW_MEMORY_EOF'`
— o texto do usuário entra por stdin, dentro de um heredoc com delimitador
entre aspas, para que o shell não expanda `$(...)`, `` ` `` nem `$VAR` e não
coma aspas. O modo argv (`-- "texto"`) continua aceito (index.md §1).

Transportado de `scripts/memory.py` do repo AmFlow — mesma lógica, alvo de
linguagem diferente: stdlib pura, Python 3.9 (docs/plan/system/language-policy.md
§3, §4). O script se auto-localiza (`Path(__file__).resolve()`) e nunca lê
`CLAUDE_PLUGIN_ROOT` do ambiente.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

TETO_CORPO = 600
FLAG = "--important"


def colapsar(texto: str) -> str:
    """Achata quebras de linha/tab em espaço, colapsa espaços e apara pontas.

    index.md §2, *Colapso*: aplicado antes do teto de 600, nunca depois.
    """
    sem_quebras = re.sub(r"[\r\n\t]+", " ", texto)
    sem_espacos_duplos = re.sub(r" {2,}", " ", sem_quebras)
    return sem_espacos_duplos.strip()


def interpretar(entrada_bruta: str) -> Tuple[bool, str]:
    """Extrai (flag_important, corpo_bruto_pre_colapso) de uma entrada já em string.

    index.md §1, *Como o script recebe a entrada* — regra sobre a string,
    nunca sobre posição de argv: `--important` só conta como flag no começo da
    entrada. Compartilhada pelos dois modos de entrada (argv e `--stdin`).
    """
    stripped = entrada_bruta.strip()

    if stripped == FLAG:
        return True, ""
    if stripped.startswith(FLAG) and stripped[len(FLAG)].isspace():
        return True, stripped[len(FLAG):]
    return False, stripped


def montar_entrada(argv: list) -> Tuple[bool, str]:
    """Modo argv: junta os argumentos e descarta um único `--` inicial."""
    entrada_bruta = " ".join(argv)

    tokens = entrada_bruta.split(None, 1)
    if tokens and tokens[0] == "--":
        entrada_bruta = tokens[1] if len(tokens) > 1 else ""

    return interpretar(entrada_bruta)


def calcular_code_span(corpo: str) -> str:
    """Delimitador de code span calculado — index.md §3, *Corpo que contém crase*.

    Uma crase a mais que a maior sequência de crases do corpo (CommonMark);
    espaço de cada lado quando o corpo começa ou termina com crase.
    """
    maior = 0
    atual = 0
    for ch in corpo:
        if ch == "`":
            atual += 1
            maior = max(maior, atual)
        else:
            atual = 0
    delimitador = "`" * (maior + 1)
    if corpo.startswith("`") or corpo.endswith("`"):
        return f"{delimitador} {corpo} {delimitador}"
    return f"{delimitador}{corpo}{delimitador}"


def resolver_autor() -> str:
    """`git config user.email`; vazio, ausente ou git indisponível → "desconhecido"."""
    try:
        resultado = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "desconhecido"
    if resultado.returncode != 0:
        return "desconhecido"
    email = resultado.stdout.strip()
    return email if email else "desconhecido"


def encontrar_projeto(cwd: Path) -> Optional[Path]:
    """Sobe de `cwd` até achar `.claude/` ou `.git/`. `None` se não achar."""
    atual = cwd.resolve()
    while True:
        if (atual / ".claude").exists() or (atual / ".git").exists():
            return atual
        if atual.parent == atual:
            return None
        atual = atual.parent


def _garantir_notes(caminho: Path) -> None:
    if not caminho.exists():
        caminho.write_text("# Memórias do usuário\n", encoding="utf-8")


def _anexar_notes(caminho: Path, bloco: str) -> None:
    _garantir_notes(caminho)
    existente = caminho.read_text(encoding="utf-8").rstrip("\n")
    novo = f"{existente}\n\n{bloco}\n" if existente else f"{bloco}\n"
    caminho.write_text(novo, encoding="utf-8")


def _garantir_important(caminho: Path) -> None:
    if not caminho.exists():
        caminho.write_text("## Memórias importantes\n", encoding="utf-8")


def _anexar_important(caminho: Path, linha: str) -> None:
    _garantir_important(caminho)
    existente = caminho.read_text(encoding="utf-8").rstrip("\n")
    if existente == "## Memórias importantes":
        novo = f"{existente}\n\n{linha}\n"
    else:
        novo = f"{existente}\n{linha}\n"
    caminho.write_text(novo, encoding="utf-8")


def processar(
    argv: list,
    project_root: Path,
    autor: str,
    data: str,
    texto: Optional[str] = None,
) -> Tuple[str, int]:
    """Valida, grava (se aceito) e devolve (mensagem, código de saída).

    `texto` preenchido é o modo `--stdin`: a entrada chegou literal, sem passar
    por argv nem pela expansão do shell. `argv` é ignorado nesse caso.

    Nenhuma recusa escreve nada — as duas checagens abaixo acontecem antes de
    qualquer `mkdir`/escrita (index.md §1, *Nenhuma recusa deixa arquivo pela
    metade*).
    """
    if texto is None:
        flag, corpo_bruto = montar_entrada(argv)
    else:
        flag, corpo_bruto = interpretar(texto)
    achatado = bool(re.search(r"[\r\n]", corpo_bruto))
    corpo = colapsar(corpo_bruto)

    if corpo == "":
        return "Uso: memory [--important] <texto>", 1
    if len(corpo) > TETO_CORPO:
        return f"Recusado: o corpo tem {len(corpo)} caracteres e o limite é 600.", 1

    memory_dir = project_root / ".claude" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    notes_path = memory_dir / "notes.md"
    important_path = memory_dir / "important.md"

    cabecalho = f"### {data} · {autor}" + (" · importante" if flag else "")
    _anexar_notes(notes_path, f"{cabecalho}\n{corpo}")

    if flag:
        _anexar_important(important_path, f"- {data}: {calcular_code_span(corpo)}")
        sucesso = (
            "Registrado em .claude/memory/notes.md e "
            f".claude/memory/important.md — {len(corpo)} caracteres."
        )
    else:
        sucesso = f"Registrado em .claude/memory/notes.md — {len(corpo)} caracteres."

    if achatado:
        return f"Aviso: quebras de linha viraram espaços.\n{sucesso}", 0
    return sucesso, 0


def main() -> None:
    cwd = Path.cwd()
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    project_root = Path(env_dir) if env_dir else encontrar_projeto(cwd)

    if project_root is None:
        print(
            "Recusado: projeto não encontrado — nem $CLAUDE_PROJECT_DIR nem "
            f".claude/ ou .git acima de {cwd}."
        )
        sys.exit(1)

    autor = resolver_autor()
    data = date.today().isoformat()

    # `--stdin`: o texto do usuário chega pelo heredoc do comando, literal.
    # É o modo que os arquivos de command usam — argv fica para uso manual e
    # para os testes que já existiam (index.md §1).
    argv = sys.argv[1:]
    texto = sys.stdin.read() if argv and argv[0] == "--stdin" else None

    mensagem, codigo = processar(argv, project_root, autor, data, texto)
    print(mensagem)
    sys.exit(codigo)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Move um arquivo markdown e mantém todos os links relativos funcionando.

Mover um .md quebra links em duas direções, e é fácil lembrar só da primeira:

  1. Links DENTRO do arquivo movido — a profundidade mudou, então `../x`
     precisa virar `../../x` (ou o contrário, ao subir).
  2. Links DE OUTROS arquivos PARA o movido — o alvo saiu do lugar.

Este script trata as duas. Ver docs/plan/system/language-policy.md.

Uso:
  ./scripts/move-md.py <origem> <destino> [--dry-run]

O destino pode ser um arquivo ou um diretório. Diretórios intermediários são
criados. Se a origem estiver versionada, usa `git mv` para preservar o
histórico.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Diretórios que nunca são varridos: read-only por norma, gerados, ou cópias.
IGNORADOS = {
    ".git",
    "node_modules",
    "legacy",
    ".next",
    "dist",
    "build",
    "worktrees",
    "__pycache__",
}

# [texto](caminho) — captura o destino para reescrever só ele.
LINK = re.compile(r"(?<=\]\()([^)\s]+)(?=\))")

# Abertura/fechamento de bloco de código: ``` ou ~~~, com qualquer nº de marcas.
FENCE = re.compile(r"^\s*(```|~~~)")

REPO_ROOT = Path(__file__).resolve().parent.parent


def e_relativo(destino: str) -> bool:
    """Só links relativos a arquivo são reescritos.

    Ficam de fora: URLs, âncoras da própria página, caminhos absolutos e
    referências mailto — nenhum deles depende de onde o arquivo está.
    """
    if not destino or destino.startswith(("#", "/", "http://", "https://", "mailto:")):
        return False
    return "://" not in destino


def separar_ancora(destino: str) -> tuple[str, str]:
    """Devolve (caminho, âncora) — a âncora sobrevive à reescrita."""
    if "#" in destino:
        caminho, _, ancora = destino.partition("#")
        return caminho, "#" + ancora
    return destino, ""


def substituir_links(conteudo: str, troca) -> str:
    """Aplica `troca` só nos links reais — nunca em exemplos.

    Documentação normativa mostra caminhos como ilustração, dentro de bloco de
    código ou entre crases. Reescrevê-los corrompe o texto: o exemplo passaria
    a mostrar o caminho de outro arquivo. A norma dev-units tem vários desses.
    """
    linhas = conteudo.split("\n")
    dentro_de_bloco = False
    saida = []

    for linha in linhas:
        if FENCE.match(linha):
            dentro_de_bloco = not dentro_de_bloco
            saida.append(linha)
            continue
        if dentro_de_bloco:
            saida.append(linha)
            continue
        # Fora de bloco, ainda há código inline: os trechos entre crases são
        # os de índice ímpar depois do split, e ficam intocados.
        partes = linha.split("`")
        for i in range(0, len(partes), 2):
            partes[i] = LINK.sub(troca, partes[i])
        saida.append("`".join(partes))

    return "\n".join(saida)


def markdowns_do_repo() -> list[Path]:
    arquivos = []
    for caminho in REPO_ROOT.rglob("*.md"):
        if any(parte in IGNORADOS for parte in caminho.relative_to(REPO_ROOT).parts):
            continue
        arquivos.append(caminho)
    return arquivos


def relativo_entre(alvo: Path, a_partir_de: Path) -> str:
    """Caminho relativo de um diretório até um alvo, no estilo POSIX.

    os.path.relpath resolve `..` corretamente e é o que o markdown espera.
    """
    import os

    return os.path.relpath(alvo, a_partir_de).replace("\\", "/")


def reescrever_links_internos(
    conteudo: str, dir_antigo: Path, dir_novo: Path
) -> tuple[str, list[tuple[str, str]]]:
    """Recalcula os links do arquivo movido a partir do novo diretório.

    Os dois diretórios são resolvidos antes de qualquer cálculo: relpath entre
    um caminho resolvido e um não-resolvido produz lixo quando há symlink no
    meio — no macOS, /tmp e /var são symlinks, então o caso é comum.
    """
    dir_antigo = dir_antigo.resolve()
    dir_novo = dir_novo.resolve()
    mudancas: list[tuple[str, str]] = []

    def troca(m: re.Match[str]) -> str:
        destino = m.group(0)
        if not e_relativo(destino):
            return destino

        caminho, ancora = separar_ancora(destino)
        alvo = (dir_antigo / caminho).resolve()

        # Link já quebrado antes da mudança: não inventar destino, preservar
        # como está para que o problema continue visível.
        if not alvo.exists():
            return destino

        novo = relativo_entre(alvo, dir_novo) + ancora
        if novo != destino:
            mudancas.append((destino, novo))
        return novo

    return substituir_links(conteudo, troca), mudancas


def reescrever_referencias(
    origem: Path, destino_final: Path, dry_run: bool
) -> list[tuple[Path, str, str]]:
    """Corrige os links de outros arquivos que apontavam para o movido."""
    origem = origem.resolve()
    destino_final = destino_final.resolve()
    aplicadas: list[tuple[Path, str, str]] = []

    for arquivo in markdowns_do_repo():
        arquivo = arquivo.resolve()
        if arquivo == origem:
            continue

        try:
            conteudo = arquivo.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        mudou = False

        def troca(m: re.Match[str]) -> str:
            nonlocal mudou
            link = m.group(0)
            if not e_relativo(link):
                return link

            caminho, ancora = separar_ancora(link)
            alvo = (arquivo.parent / caminho).resolve()
            if alvo != origem:
                return link

            novo = relativo_entre(destino_final, arquivo.parent) + ancora
            if novo != link:
                mudou = True
                aplicadas.append((arquivo, link, novo))
            return novo

        novo_conteudo = substituir_links(conteudo, troca)
        if mudou and not dry_run:
            arquivo.write_text(novo_conteudo, encoding="utf-8")

    return aplicadas


def esta_versionado(caminho: Path) -> bool:
    resultado = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(caminho)],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return resultado.returncode == 0


def mover(origem: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if esta_versionado(origem):
        subprocess.run(
            ["git", "mv", str(origem), str(destino)], cwd=REPO_ROOT, check=True
        )
    else:
        origem.rename(destino)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origem")
    parser.add_argument("destino")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="mostra o que mudaria, sem tocar em nada",
    )
    args = parser.parse_args()

    origem = Path(args.origem).resolve()
    if not origem.is_file():
        print(f"erro: origem não existe — {args.origem}", file=sys.stderr)
        return 1
    if origem.suffix != ".md":
        print(f"erro: origem não é markdown — {args.origem}", file=sys.stderr)
        return 1

    destino = Path(args.destino)
    if destino.is_dir() or args.destino.endswith("/"):
        destino = destino / origem.name
    destino = destino.resolve()

    if destino.exists():
        print(f"erro: destino já existe — {args.destino}", file=sys.stderr)
        return 1

    conteudo = origem.read_text(encoding="utf-8")
    novo_conteudo, internos = reescrever_links_internos(
        conteudo, origem.parent, destino.parent
    )

    referencias = reescrever_referencias(origem, destino, dry_run=True)

    rel_origem = origem.relative_to(REPO_ROOT)
    rel_destino = destino.relative_to(REPO_ROOT)
    print(f"{rel_origem}  ->  {rel_destino}")

    print(f"\nlinks dentro do arquivo: {len(internos)} a corrigir")
    for antigo, novo in internos:
        print(f"  {antigo}  ->  {novo}")

    print(f"\nreferências de outros arquivos: {len(referencias)} a corrigir")
    for arquivo, antigo, novo in referencias:
        print(f"  {arquivo.relative_to(REPO_ROOT)}: {antigo}  ->  {novo}")

    if args.dry_run:
        print("\n(dry-run — nada foi alterado)")
        return 0

    mover(origem, destino)
    destino.write_text(novo_conteudo, encoding="utf-8")
    reescrever_referencias(origem, destino, dry_run=False)

    print("\nmovido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

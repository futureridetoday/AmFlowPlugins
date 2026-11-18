#!/usr/bin/env python3
"""`fetch_package.py` — baixa, confere e instala os pacotes que `install` ou `update` devolveram.

Duas fases, com a M10 entre elas (index.md §9.4 do plano 0028):

  fetch_package.py baixar --raiz <raiz>               (stdin: o array `packages`, como a tool devolveu)
  fetch_package.py aplicar --raiz <raiz> --area <area>
  fetch_package.py descartar --raiz <raiz> --area <area>   (cancelamento na M10: apaga a <area>)

`<raiz>` é a pasta que contém `.claude/`: o projeto no `install`, o diretório home em `get`, `sync` e
`hub-update`. Sem credencial: o link é a permissão. Em falha, nenhum recurso instalado é alterado.

Saída: linhas `AREA`, `PACOTE`, `ARQUIVO`, `INSTALADO` e `RESULTADO: OK|ERRO` (com `MOTIVO:`); nunca o
conteúdo de arquivo. Códigos de saída (§9.5): 0 concluído; 2 chamada inválida; 10 transporte;
11 integridade; 12 pacote inválido; 13 destino; 20 sem egress.

Cross-repo: nasce aqui e desce a `plugins/worker/scripts/` do AmFlowPlugins pelo `vendor.py`.
Python 3.9+, stdlib pura.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from fetch_package_app import aplicar, baixar, descartar
from fetch_package_domain import EXIT_USO
from fetch_package_infra import Disco


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print("RESULTADO: ERRO")
        print(f"MOTIVO: uso: {message}")
        sys.exit(EXIT_USO)


def main(argv=None, entrada=None, disco=None) -> int:
    parser = _Parser(prog="fetch_package.py")
    sub = parser.add_subparsers(dest="fase", required=True, parser_class=_Parser)
    fase1 = sub.add_parser("baixar")
    fase1.add_argument("--raiz", required=True)
    fase2 = sub.add_parser("aplicar")
    fase2.add_argument("--raiz", required=True)
    fase2.add_argument("--area", required=True)
    fase3 = sub.add_parser("descartar")
    fase3.add_argument("--raiz", required=True)
    fase3.add_argument("--area", required=True)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    raiz = os.path.abspath(os.path.expanduser(args.raiz))
    if not os.path.isdir(raiz):
        print("RESULTADO: ERRO")
        print(f"MOTIVO: a raiz `{raiz}` não é uma pasta")
        return EXIT_USO
    disco = Disco() if disco is None else disco

    if args.fase == "baixar":
        texto = (sys.stdin if entrada is None else entrada).read()
        try:
            bruto = json.loads(texto)
        except ValueError:
            print("RESULTADO: ERRO")
            print("MOTIVO: a entrada não é JSON — esperado o array `packages`")
            return EXIT_USO
        codigo, linhas = baixar(bruto, raiz, disco)
    else:
        funcao = aplicar if args.fase == "aplicar" else descartar
        codigo, linhas = funcao(raiz, os.path.abspath(os.path.expanduser(args.area)), disco)
    for linha in linhas:
        print(linha)
    return codigo


if __name__ == "__main__":
    sys.exit(main())

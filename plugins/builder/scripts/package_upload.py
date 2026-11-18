#!/usr/bin/env python3
"""`package_upload.py` — envia o zip do recurso ao link assinado do storage.

Uso:
  AMFLOW_PACKAGE_SHA256=<sha> AMFLOW_PACKAGE_SIZE=<bytes> package_upload.py <PACKAGE> <upload_url>

`<PACKAGE>` é o caminho que o `publish.py` imprimiu; SHA-256 e tamanho vão no ambiente, não em
argumento, para o modelo transcrever só o caminho e o link. Sem credencial: o link é a permissão.

Imprime `RESULTADO: OK` ou `RESULTADO: ERRO` com `MOTIVO:`. Códigos de saída (index.md §9.3 do plano
0028): 0 enviado; 2 chamada inválida; 10 transporte; 11 o arquivo mudou desde o `publish.py`;
13 o zip não abre; 20 sem conexão com o domínio do link.

Cross-repo: nasce aqui e desce a `plugins/builder/scripts/` do AmFlowPlugins pelo `vendor.py`.
Python 3.9+, stdlib pura.
"""

from __future__ import annotations

import os
import sys

from package_upload_app import enviar
from package_upload_domain import EXIT_OK, EXIT_USO
from package_upload_infra import ler_bytes, put_pacote


def main(argv=None, ambiente=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ambiente = os.environ if ambiente is None else ambiente
    if len(argv) != 2:
        print("RESULTADO: ERRO")
        print("MOTIVO: uso: package_upload.py <PACKAGE> <upload_url>")
        return EXIT_USO
    codigo, motivo = enviar(
        argv[0],
        argv[1],
        ambiente.get("AMFLOW_PACKAGE_SHA256"),
        ambiente.get("AMFLOW_PACKAGE_SIZE"),
        ler_bytes,
        put_pacote,
    )
    print("RESULTADO: OK" if codigo == EXIT_OK else "RESULTADO: ERRO")
    if motivo:
        print(f"MOTIVO: {motivo}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())

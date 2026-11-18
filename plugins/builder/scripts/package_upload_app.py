"""`package_upload_app.py` — o caso de uso do envio: confere o zip local e faz o `PUT` no link.

Não toca disco nem rede: `ler` e `put` chegam por argumento (norma `clean-architecture.md`, seção 5).
Devolve `(código de saída, motivo)`; `motivo` é `None` quando enviou.
"""

from __future__ import annotations

from package_upload_domain import (
    EXIT_INTEGRIDADE,
    EXIT_OK,
    EXIT_ORIGEM,
    EXIT_SEM_EGRESS,
    EXIT_TRANSPORTE,
    EXIT_USO,
    FalhaTransporte,
    SemEgress,
    sha256_hex,
    sha256_valido,
    url_valida,
)


def enviar(caminho, url, sha256_declarado, tamanho_declarado, ler, put):
    """`ler(caminho) -> bytes` levanta `OSError` se o arquivo não abre; `put(url, dados) -> int`
    devolve o status HTTP, ou levanta `SemEgress` / `FalhaTransporte`."""
    if not caminho or not url:
        return EXIT_USO, "uso: package_upload.py <PACKAGE> <upload_url>"
    if not url_valida(url):
        return EXIT_USO, "o link precisa ser http ou https"
    if not sha256_valido(sha256_declarado or ""):
        return EXIT_USO, "AMFLOW_PACKAGE_SHA256 ausente ou fora do formato (64 hex minúsculos)"
    try:
        tamanho = int(tamanho_declarado or "")
    except ValueError:
        return EXIT_USO, "AMFLOW_PACKAGE_SIZE ausente ou não é inteiro"

    try:
        dados = ler(caminho)
    except OSError as exc:
        return EXIT_ORIGEM, f"o pacote não pode ser lido — {caminho}: {exc}"

    if len(dados) != tamanho or sha256_hex(dados) != sha256_declarado:
        return EXIT_INTEGRIDADE, "o pacote mudou depois do publish.py (tamanho ou SHA-256 diferentes dos declarados)"

    try:
        status = put(url, dados)
    except SemEgress as exc:
        return EXIT_SEM_EGRESS, f"sem conexão com o domínio do link — {exc}"
    except FalhaTransporte as exc:
        return EXIT_TRANSPORTE, f"falha de transporte — {exc}"

    if 200 <= status < 300:
        return EXIT_OK, None
    return EXIT_TRANSPORTE, f"o storage respondeu {status}"

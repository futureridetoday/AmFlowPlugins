"""`package_upload_domain.py` — regra pura do pacote que o Builder envia ao Hub.

Fonte dos nomes, limites e códigos: `docs/plan/hub/0028-decouple-resource-transport/index.md`
(seções 2.3, 9 e 12). Este arquivo não importa disco, rede nem processo — a norma
`clean-architecture.md` (seção 5 e guarda 6.3) o proíbe; o que toca disco e rede mora em
`package_upload_infra.py`.

Cópia dos limites da seção 12: o teste `test_transport_limits_parity.py` a confere contra a tabela.
Compatível com Python 3.9 (L-02).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# Entrada reservada do secure-invite, na raiz do zip, fora de `.claude/` (seção 2.3).
SECURE_INVITE_ENTRY = "amflow-secure-invite.jws"

# Limites — fonte única: tabela da seção 12 do index.md.
MAX_FILE_BYTES = 1048576
MAX_CONTENT_BYTES = 10485760
MAX_PACKAGE_BYTES = 11534336
MAX_PACKAGE_FILES = 100

# Códigos de saída do script de envio (seção 9.3).
EXIT_OK = 0
EXIT_USO = 2
EXIT_TRANSPORTE = 10
EXIT_INTEGRIDADE = 11
EXIT_ORIGEM = 13
EXIT_SEM_EGRESS = 20

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class SemEgress(Exception):
    """Falha antes de haver resposta HTTP: o domínio do link não foi alcançado (código 20)."""


class FalhaTransporte(Exception):
    """Falha de transporte depois de a conexão abrir: reset, timeout, leitura truncada (código 10)."""


@dataclass
class Pacote:
    caminho: str
    sha256: str
    tamanho: int


def sha256_hex(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_valido(valor: str) -> bool:
    return bool(_SHA256_RE.fullmatch(valor or ""))


def url_valida(url: str) -> bool:
    """Só `http` e `https`: o `urllib` também abre `file:` e `ftp:`, e o link é argumento vindo da
    conversa."""
    return url.startswith("https://") or url.startswith("http://")


def verificar_conteudo(arquivos: dict[str, str], secure_invite: str) -> str | None:
    """Motivo da recusa, ou `None`. Os limites contam só os arquivos do recurso — a entrada reservada
    fica de fora do número de arquivos e da soma (seção 2.3)."""
    if len(arquivos) > MAX_PACKAGE_FILES:
        return f"o recurso tem {len(arquivos)} arquivos; o limite é {MAX_PACKAGE_FILES}"
    total = 0
    for caminho in sorted(arquivos):
        tamanho = len(arquivos[caminho].encode("utf-8"))
        if tamanho > MAX_FILE_BYTES:
            return f"`{caminho}` tem {tamanho} bytes; o limite por arquivo é {MAX_FILE_BYTES}"
        total += tamanho
    if total > MAX_CONTENT_BYTES:
        return f"o conteúdo soma {total} bytes; o limite é {MAX_CONTENT_BYTES}"
    linha = secure_invite.strip()
    if not linha or "\n" in linha or "\r" in linha or not linha.isascii():
        return "o secure-invite deve ser texto ASCII de uma linha"
    return None


def verificar_tamanho_pacote(tamanho: int) -> str | None:
    if tamanho > MAX_PACKAGE_BYTES:
        return f"o pacote tem {tamanho} bytes; o limite é {MAX_PACKAGE_BYTES}"
    return None


def montar_entradas(arquivos: dict[str, str], secure_invite: str) -> list[tuple[str, bytes]]:
    """Entradas do zip, em ordem estável: os arquivos do recurso por caminho e, por último, a entrada
    reservada com o JWS em uma linha, sem quebra final. Não há manifesto nem entrada de diretório
    (seção 2.1)."""
    entradas = [(caminho, arquivos[caminho].encode("utf-8")) for caminho in sorted(arquivos)]
    entradas.append((SECURE_INVITE_ENTRY, secure_invite.strip().encode("ascii")))
    return entradas

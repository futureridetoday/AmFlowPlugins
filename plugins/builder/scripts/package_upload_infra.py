"""`package_upload_infra.py` — disco e rede do envio: grava o zip e faz o `PUT` no link.

Stdlib pura, compatível com Python 3.9. A regra mora em `package_upload_domain.py`.
"""

from __future__ import annotations

import errno
import http.client
import socket
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from package_upload_domain import FalhaTransporte, Pacote, SemEgress, sha256_hex

# Data fixa: zipar o mesmo conteúdo duas vezes dá os mesmos bytes. Nenhum consumidor dá
# significado a data, permissão ou comentário de entrada (seção 2.1).
_DATA_ENTRADA = (1980, 1, 1, 0, 0, 0)
_ERRNO_SEM_ROTA = (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN)
_TIMEOUT_SEGUNDOS = 60


def gravar_pacote(entradas: list[tuple[str, bytes]]) -> Pacote:
    """Grava o zip, todas as entradas "armazenadas", numa pasta temporária nova."""
    pasta = Path(tempfile.mkdtemp(prefix="amflow-pacote-"))
    caminho = pasta / "pacote.zip"
    with zipfile.ZipFile(caminho, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as zf:
        for nome, dados in entradas:
            info = zipfile.ZipInfo(nome, date_time=_DATA_ENTRADA)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            zf.writestr(info, dados)
    bytes_zip = caminho.read_bytes()
    return Pacote(str(caminho), sha256_hex(bytes_zip), len(bytes_zip))


def descartar_pacote(pacote: Pacote) -> None:
    caminho = Path(pacote.caminho)
    caminho.unlink()
    caminho.parent.rmdir()


def ler_bytes(caminho: str) -> bytes:
    return Path(caminho).read_bytes()


def _sem_conexao(motivo) -> bool:
    """Falha antes de haver resposta HTTP: nome não resolve, conexão recusada, rota ausente, proxy
    recusando o túnel (S-9 do index.md — o critério é o que o script observa)."""
    if isinstance(motivo, (socket.gaierror, ConnectionRefusedError)):
        return True
    if isinstance(motivo, OSError):
        if motivo.errno in _ERRNO_SEM_ROTA:
            return True
        if "Tunnel connection failed" in str(motivo):
            return True
    return False


def put_pacote(url: str, dados: bytes) -> int:
    """`PUT` dos bytes crus, `Content-Type: application/zip` (S-7). Devolve o status HTTP."""
    pedido = urllib.request.Request(
        url, data=dados, method="PUT", headers={"Content-Type": "application/zip"}
    )
    try:
        with urllib.request.urlopen(pedido, timeout=_TIMEOUT_SEGUNDOS) as resposta:
            return resposta.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except urllib.error.URLError as exc:
        if _sem_conexao(exc.reason):
            raise SemEgress(str(exc.reason))
        raise FalhaTransporte(str(exc.reason))
    except (OSError, http.client.HTTPException) as exc:
        raise FalhaTransporte(str(exc))

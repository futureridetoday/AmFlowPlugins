"""`fetch_package_infra.py` — disco e rede do recebimento: baixa, lê o zip, extrai, move e apaga.

Stdlib pura, compatível com Python 3.9. A regra mora em `fetch_package_domain.py`; a sequência dos
passos, em `fetch_package_app.py`. Nada aqui decide o que é válido — só executa e traduz a falha do
sistema no código de saída da seção 9.5 do index.md.
"""

from __future__ import annotations

import errno
import hashlib
import http.client
import json
import os
import shutil
import socket
import urllib.error
import urllib.request
import uuid
import zipfile
import zlib

from fetch_package_domain import (
    EXIT_DESTINO,
    EXIT_PACOTE_INVALIDO,
    EXIT_USO,
    Entrada,
    FalhaDoWorker,
    FalhaTransporte,
    SemEgress,
)

_ERRNO_SEM_ROTA = (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN)
_TIMEOUT_SEGUNDOS = 60
_BLOCO = 65536
TMP = ".amflow-tmp"
RESERVA = ".amflow-reserva"


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


class Disco:
    """O acesso a disco e rede que o caso de uso recebe por argumento."""

    # ── caminhos ────────────────────────────────────────────────────────────────────────────────
    def juntar(self, base: str, *partes: str) -> str:
        """Junta `base` com caminhos relativos escritos com `/`."""
        caminho = base
        for parte in partes:
            for segmento in parte.split("/"):
                if segmento:
                    caminho = os.path.join(caminho, segmento)
        return caminho

    def existe(self, caminho: str) -> bool:
        """`lexists`: um link simbólico quebrado também ocupa o lugar."""
        return os.path.lexists(caminho)

    def listar(self, caminho: str) -> list[str]:
        try:
            return sorted(os.listdir(caminho))
        except (FileNotFoundError, NotADirectoryError):
            return []

    # ── mover e apagar ──────────────────────────────────────────────────────────────────────────
    def mover(self, origem: str, destino: str) -> None:
        """Uma renomeação, no mesmo sistema de arquivos (L-06, item 3)."""
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        os.replace(origem, destino)

    def apagar(self, caminho: str) -> None:
        if os.path.islink(caminho) or os.path.isfile(caminho):
            os.unlink(caminho)
        elif os.path.isdir(caminho):
            shutil.rmtree(caminho)

    def remover_se_vazio(self, caminho: str) -> None:
        """Remove a pasta e as subpastas que ficaram vazias; o que tem arquivo fica."""
        if os.path.islink(caminho) or not os.path.isdir(caminho):
            return
        for filho in os.listdir(caminho):
            self.remover_se_vazio(os.path.join(caminho, filho))
        try:
            os.rmdir(caminho)
        except OSError:
            pass

    # ── texto ───────────────────────────────────────────────────────────────────────────────────
    def ler_texto(self, caminho: str) -> str:
        with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
            return arquivo.read()

    def escrever_texto(self, caminho: str, texto: str) -> None:
        """Reescreve o arquivo, mantendo a permissão que ele tem."""
        modo = os.stat(caminho).st_mode & 0o777
        with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.write(texto)
        os.chmod(caminho, modo)

    # ── destino (seção 10.1) ────────────────────────────────────────────────────────────────────
    def verificar_destino(self, raiz: str, relativo: str) -> None:
        """O caminho resolvido tem de ficar dentro de `<raiz>/.claude/`, e nem o destino nem um
        componente existente dele pode ser link simbólico. Código 13."""
        claude = os.path.realpath(self.juntar(raiz, ".claude"))
        atual = self.juntar(raiz, ".claude")
        for segmento in relativo.split("/")[1:]:
            atual = os.path.join(atual, segmento)
            if os.path.islink(atual):
                raise FalhaDoWorker(EXIT_DESTINO, f"`{atual}` é link simbólico; o Worker não instala por cima de um")
        real = os.path.realpath(self.juntar(raiz, relativo))
        if os.path.commonpath([claude, real]) != claude or real == claude:
            raise FalhaDoWorker(EXIT_DESTINO, f"o destino resolve para fora de `{claude}`: {real}")

    # ── área temporária ─────────────────────────────────────────────────────────────────────────
    def criar_area(self, raiz: str) -> str:
        """`<raiz>/.claude/.amflow-tmp/<id>/` — dentro de `.claude/`, no mesmo sistema de arquivos
        do destino (seção 9.4)."""
        area = self.juntar(raiz, ".claude", TMP, uuid.uuid4().hex)
        try:
            os.makedirs(area)
        except OSError as exc:
            raise FalhaDoWorker(EXIT_DESTINO, f"não foi possível criar `{area}`: {exc}")
        return area

    def validar_area(self, raiz: str, area: str) -> None:
        """A `--area` que a fase 2 recebe é argumento vindo da conversa: só vale se for filha direta de
        `.amflow-tmp` e existir."""
        tmp = os.path.realpath(self.juntar(raiz, ".claude", TMP))
        real = os.path.realpath(area)
        if os.path.dirname(real) != tmp or not os.path.isdir(real):
            raise FalhaDoWorker(EXIT_USO, "a `--area` não é uma área criada pela fase 1 desta raiz")

    def apagar_area(self, raiz: str, area: str) -> None:
        shutil.rmtree(area, ignore_errors=True)
        self.remover_se_vazio(self.juntar(raiz, ".claude", TMP))
        self.remover_se_vazio(self.juntar(raiz, ".claude", RESERVA))

    def gravar_pacotes(self, area: str, registros: list[dict]) -> None:
        with open(os.path.join(area, "pacotes.json"), "w", encoding="utf-8") as arquivo:
            json.dump(registros, arquivo, ensure_ascii=False)

    def ler_pacotes(self, area: str):
        try:
            with open(os.path.join(area, "pacotes.json"), "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except (OSError, ValueError) as exc:
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"pacotes.json ilegível: {exc}")

    # ── rede ────────────────────────────────────────────────────────────────────────────────────
    def baixar(self, url: str, area: str, nome_zip: str, limite: int) -> tuple[int, str]:
        """Baixa para `<area>/<nome_zip>`. Devolve `(bytes gravados, SHA-256)`. Para de ler quando passa
        de `limite` — o excesso já é divergência de tamanho. Sem credencial: o link é a permissão."""
        pedido = urllib.request.Request(url, method="GET")
        destino = os.path.join(area, nome_zip)
        total = 0
        resumo = hashlib.sha256()
        try:
            with urllib.request.urlopen(pedido, timeout=_TIMEOUT_SEGUNDOS) as resposta:
                if not 200 <= resposta.status < 300:
                    raise FalhaTransporte(f"o storage respondeu {resposta.status}")
                with open(destino, "wb") as saida:
                    while total <= limite:
                        bloco = resposta.read(_BLOCO)
                        if not bloco:
                            break
                        total += len(bloco)
                        resumo.update(bloco)
                        saida.write(bloco)
        except urllib.error.HTTPError as exc:
            # Link vencido ou revogado chega aqui como 4xx; o texto não leva a URL (carrega o token).
            raise FalhaTransporte(f"o storage respondeu {exc.code}")
        except urllib.error.URLError as exc:
            if _sem_conexao(exc.reason):
                raise SemEgress(str(exc.reason))
            raise FalhaTransporte(str(exc.reason))
        except (OSError, http.client.HTTPException) as exc:
            if isinstance(exc, (socket.gaierror, ConnectionRefusedError)) or (
                isinstance(exc, OSError) and exc.errno in _ERRNO_SEM_ROTA
            ):
                raise SemEgress(str(exc))
            raise FalhaTransporte(str(exc))
        return total, resumo.hexdigest()

    def hash_arquivo(self, area: str, nome_zip: str) -> tuple[int, str]:
        resumo = hashlib.sha256()
        total = 0
        try:
            with open(os.path.join(area, nome_zip), "rb") as arquivo:
                while True:
                    bloco = arquivo.read(_BLOCO)
                    if not bloco:
                        break
                    total += len(bloco)
                    resumo.update(bloco)
        except OSError as exc:
            raise FalhaDoWorker(EXIT_DESTINO, f"não foi possível ler `{nome_zip}` da área: {exc}")
        return total, resumo.hexdigest()

    # ── zip ─────────────────────────────────────────────────────────────────────────────────────
    def ler_entradas(self, area: str, nome_zip: str) -> list[Entrada]:
        """O diretório central do zip, sem ler conteúdo."""
        try:
            with zipfile.ZipFile(os.path.join(area, nome_zip)) as zf:
                return [
                    Entrada(i.filename, i.file_size, i.compress_size, i.compress_type, i.external_attr)
                    for i in zf.infolist()
                ]
        except (zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError, EOFError) as exc:
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"pacote inválido (unreadable_zip): {exc}")
        except OSError as exc:
            raise FalhaDoWorker(EXIT_DESTINO, f"não foi possível abrir `{nome_zip}`: {exc}")

    def extrair(self, area: str, nome_zip: str, entradas: list[Entrada], modo) -> None:
        """Extrai cada entrada para `<area>/extraido/<nome da entrada>`, com a permissão de `modo(nome)`
        — nunca a do zip. O caminho resolvido tem de ficar dentro de `extraido/`."""
        base = os.path.realpath(os.path.join(area, "extraido"))
        try:
            with zipfile.ZipFile(os.path.join(area, nome_zip)) as zf:
                for entrada in entradas:
                    destino = os.path.realpath(os.path.join(base, *entrada.nome.split("/")))
                    if os.path.commonpath([base, destino]) != base or destino == base:
                        raise FalhaDoWorker(EXIT_DESTINO, f"`{entrada.nome}` resolve para fora da área")
                    dados = zf.read(entrada.nome)
                    if len(dados) != entrada.tamanho:
                        raise FalhaDoWorker(
                            EXIT_PACOTE_INVALIDO, f"pacote inválido (size_inconsistent): `{entrada.nome}`"
                        )
                    os.makedirs(os.path.dirname(destino), exist_ok=True)
                    with open(destino, "wb") as saida:
                        saida.write(dados)
                    os.chmod(destino, modo(entrada.nome))
        except (zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError, RuntimeError, EOFError, zlib.error) as exc:
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"pacote inválido (unreadable_zip): {exc}")
        except OSError as exc:
            raise FalhaDoWorker(EXIT_DESTINO, f"não foi possível extrair `{nome_zip}`: {exc}")

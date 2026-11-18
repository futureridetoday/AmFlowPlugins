"""`fetch_package_domain.py` — regra pura do pacote que o Worker recebe do Hub.

Fonte dos nomes, limites e códigos: `docs/plan/hub/0028-decouple-resource-transport/index.md`
(seções 2.2, 2.3, 9.4, 9.5, 10.1 a 10.3 e 12). Este arquivo não importa disco, rede nem processo — a
norma `clean-architecture.md` (seção 5 e guarda 6.3) o proíbe; o que toca disco e rede mora em
`fetch_package_infra.py`. O Worker não importa o domínio do Builder (isolamento entre plugins): as
cópias abaixo são do lado dele e o teste `test_transport_limits_parity.py` as confere.

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
MAX_PACKAGE_FILES = 100

# Códigos de saída do Worker (seção 9.5).
EXIT_OK = 0
EXIT_USO = 2
EXIT_TRANSPORTE = 10
EXIT_INTEGRIDADE = 11
EXIT_PACOTE_INVALIDO = 12
EXIT_DESTINO = 13
EXIT_SEM_EGRESS = 20

TIPOS = ("skill", "agent", "command", "hook")

# Tipo de arquivo de `external_attr` (bits altos): link simbólico (S-4).
_MASCARA_TIPO = 0o170000
_LINK_SIMBOLICO = 0o120000
_METODO_ARMAZENADO = 0

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class FalhaDoWorker(Exception):
    """Falha com código de saída próprio; `codigo` é o da seção 9.5 e `motivo` o texto para o usuário."""

    def __init__(self, codigo: int, motivo: str):
        super().__init__(motivo)
        self.codigo = codigo
        self.motivo = motivo


class SemEgress(Exception):
    """Falha antes de haver resposta HTTP: o domínio do link não foi alcançado (código 20)."""


class FalhaTransporte(Exception):
    """Falha de transporte depois de a conexão abrir: reset, timeout, leitura truncada (código 10)."""


@dataclass
class Entrada:
    """O que o Worker lê do diretório central de uma entrada do zip, sem o conteúdo."""

    nome: str
    tamanho: int
    tamanho_comprimido: int
    metodo: int
    external_attr: int


@dataclass
class Registro:
    """O que a fase 1 grava em `pacotes.json` para a fase 2: o item sem o link, mais o zip baixado."""

    tipo: str
    nome: str
    versao: str
    zip: str
    sha256: str
    tamanho: int
    arquivos: int


@dataclass
class Item:
    """Um item do array `packages` que `install` ou `update` devolveu (seção 7.3)."""

    role: str
    tipo: str
    nome: str
    versao: str
    download_url: str
    sha256: str
    tamanho: int
    arquivos: int


def sha256_hex(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_valido(valor) -> bool:
    return isinstance(valor, str) and bool(_SHA256_RE.fullmatch(valor))


def url_valida(url) -> bool:
    """Só `http` e `https`: o link vem de resposta da tool e o `urllib` também abre `file:` e `ftp:`."""
    return isinstance(url, str) and (url.startswith("https://") or url.startswith("http://"))


def validar_tipo_e_nome(tipo, nome) -> str | None:
    """Motivo da recusa (código 12), ou `None` (seção 10.1)."""
    if tipo not in TIPOS:
        return f"tipo `{tipo}` fora de skill, agent, command e hook"
    if not isinstance(nome, str) or nome in ("", ".", ".."):
        return f"nome de recurso `{nome}` inválido"
    if "/" in nome or "\\" in nome or "\x00" in nome:
        return f"nome de recurso `{nome}` tem separador ou NUL"
    return None


def interpretar_itens(bruto) -> list[Item]:
    """Valida o array `packages` e devolve os itens. Levanta `FalhaDoWorker` (2 se não é o formato
    da tool, 12 se o conteúdo do item é inconsistente)."""
    if isinstance(bruto, dict):
        bruto = bruto.get("packages")
    if not isinstance(bruto, list) or not bruto:
        raise FalhaDoWorker(EXIT_USO, "a entrada deve ser o array `packages` da tool, não vazio")
    itens: list[Item] = []
    vistos: set[tuple[str, str]] = set()
    for posicao, cru in enumerate(bruto):
        if not isinstance(cru, dict):
            raise FalhaDoWorker(EXIT_USO, f"packages[{posicao}] não é um objeto")
        tipo, nome = cru.get("type"), cru.get("name")
        motivo = validar_tipo_e_nome(tipo, nome)
        if motivo:
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"packages[{posicao}]: {motivo}")
        versao = cru.get("version")
        if not isinstance(versao, str) or not versao or any(c in versao for c in " \n\r\x00"):
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"packages[{posicao}]: versão inválida")
        if not url_valida(cru.get("download_url")):
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"packages[{posicao}]: download_url deve ser http ou https")
        if not sha256_valido(cru.get("sha256")):
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"packages[{posicao}]: sha256 fora do formato (64 hex minúsculos)")
        tamanho, arquivos = cru.get("size_bytes"), cru.get("file_count")
        for campo, valor in (("size_bytes", tamanho), ("file_count", arquivos)):
            if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
                raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"packages[{posicao}]: {campo} deve ser inteiro positivo")
        if (tipo, nome) in vistos:
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"`{tipo}/{nome}` aparece mais de uma vez em packages")
        vistos.add((tipo, nome))
        itens.append(
            Item(
                role=str(cru.get("role") or ""),
                tipo=tipo,
                nome=nome,
                versao=versao,
                download_url=cru["download_url"],
                sha256=cru["sha256"],
                tamanho=tamanho,
                arquivos=arquivos,
            )
        )
    return itens


def interpretar_registros(bruto) -> list[Registro]:
    """Valida o `pacotes.json` lido da `<area>` — o tempo entre as fases é o da M10, e a pasta pode
    ter mudado. Levanta `FalhaDoWorker` com o código 12."""
    if not isinstance(bruto, list) or not bruto:
        raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, "pacotes.json ausente, vazio ou fora do formato")
    registros: list[Registro] = []
    for posicao, cru in enumerate(bruto):
        if not isinstance(cru, dict):
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"pacotes.json[{posicao}] não é um objeto")
        motivo = validar_tipo_e_nome(cru.get("type"), cru.get("name"))
        arquivo = cru.get("zip")
        if motivo is None and not (isinstance(arquivo, str) and re.fullmatch(r"\d+\.zip", arquivo)):
            motivo = "nome de zip fora do formato"
        if motivo is None and not sha256_valido(cru.get("sha256")):
            motivo = "sha256 fora do formato"
        for campo in ("size_bytes", "file_count"):
            valor = cru.get(campo)
            if motivo is None and (isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0):
                motivo = f"{campo} deve ser inteiro positivo"
        versao = cru.get("version")
        if motivo is None and not (isinstance(versao, str) and versao):
            motivo = "versão inválida"
        if motivo:
            raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"pacotes.json[{posicao}]: {motivo}")
        registros.append(
            Registro(cru["type"], cru["name"], versao, arquivo, cru["sha256"], cru["size_bytes"], cru["file_count"])
        )
    return registros


def conferir_download(item, tamanho: int, sha256: str) -> None:
    """Tamanho ou SHA-256 divergente do que o Hub declarou: código 11."""
    if tamanho != item.tamanho:
        raise FalhaDoWorker(
            EXIT_INTEGRIDADE, f"`{item.tipo}/{item.nome}`: {tamanho} bytes baixados, o Hub declarou {item.tamanho}"
        )
    if sha256 != item.sha256:
        raise FalhaDoWorker(EXIT_INTEGRIDADE, f"`{item.tipo}/{item.nome}`: SHA-256 diferente do declarado")


def candidatos_do_destino(tipo: str, nome: str) -> list[str]:
    """Caminhos, relativos à `<raiz>`, que a instalação de `<tipo>/<nome>` ocupa ou pode ocupar. O agent
    tem dois layouts (seção 2.2): quem se instala num pode ter um resto do outro."""
    if tipo == "agent":
        return [f".claude/agents/{nome}", f".claude/agents/{nome}.md"]
    if tipo == "command":
        return [f".claude/commands/{nome}.md"]
    return [f".claude/{tipo}s/{nome}"]


def _caminho_escapa(nome: str) -> bool:
    if not nome or nome.startswith("/") or "\\" in nome or "\x00" in nome or "//" in nome:
        return True
    return any(segmento in (".", "..", "") for segmento in nome.split("/"))


def inspecionar_entradas(tipo: str, nome: str, entradas: list[Entrada]) -> tuple[list[Entrada], str]:
    """Aplica as regras das seções 3 e 10.1 que o Worker consegue ver. Devolve os arquivos do recurso
    (sem a reservada) e o destino da unidade de troca, relativo à `<raiz>`. Levanta `FalhaDoWorker`
    com o código 12.

    A entrada reservada é ignorada: não é extraída, não é listada, não conta (seção 10.1)."""
    motivo = validar_tipo_e_nome(tipo, nome)
    if motivo:
        raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, motivo)

    def recusa(codigo: str, nome_da_entrada: str) -> FalhaDoWorker:
        return FalhaDoWorker(EXIT_PACOTE_INVALIDO, f"pacote inválido ({codigo}): `{nome_da_entrada}`")

    vistos: set[str] = set()
    arquivos: list[Entrada] = []
    for entrada in entradas:
        if entrada.nome in vistos:
            raise recusa("duplicate_entry", entrada.nome)
        vistos.add(entrada.nome)
        if entrada.nome == SECURE_INVITE_ENTRY:
            continue
        # A barra final é o que distingue a entrada de diretório; sem ela o segmento vazio de `a/b/`
        # a faria passar por `path_escape`.
        sem_barra_final = entrada.nome[:-1] if entrada.nome.endswith("/") else entrada.nome
        if _caminho_escapa(sem_barra_final):
            raise recusa("path_escape", entrada.nome)
        if entrada.nome.endswith("/"):
            raise recusa("directory_entry", entrada.nome)
        if (entrada.external_attr >> 16) & _MASCARA_TIPO == _LINK_SIMBOLICO:
            raise recusa("symlink", entrada.nome)
        if entrada.metodo != _METODO_ARMAZENADO:
            raise recusa("method_not_stored", entrada.nome)
        arquivos.append(entrada)

    if not arquivos:
        raise FalhaDoWorker(EXIT_PACOTE_INVALIDO, "pacote sem arquivos do recurso")

    plano_agent = f".claude/agents/{nome}.md"
    if tipo == "command" or (tipo == "agent" and any(e.nome == plano_agent for e in arquivos)):
        # Layout de arquivo único: exatamente o `.md`, e mais nada.
        destino = plano_agent if tipo == "agent" else f".claude/commands/{nome}.md"
        prefixo = None
    else:
        destino = f".claude/{tipo}s/{nome}"
        prefixo = destino + "/"
    for entrada in arquivos:
        if prefixo is None:
            dentro = entrada.nome == destino
        else:
            dentro = entrada.nome.startswith(prefixo) and len(entrada.nome) > len(prefixo)
        if not dentro:
            raise recusa("outside_prefix", entrada.nome)

    if len(arquivos) > MAX_PACKAGE_FILES:
        raise FalhaDoWorker(
            EXIT_PACOTE_INVALIDO, f"pacote com {len(arquivos)} arquivos; o limite é {MAX_PACKAGE_FILES}"
        )
    total = 0
    for entrada in arquivos:
        if entrada.tamanho > MAX_FILE_BYTES:
            raise FalhaDoWorker(
                EXIT_PACOTE_INVALIDO,
                f"`{entrada.nome}` tem {entrada.tamanho} bytes; o limite por arquivo é {MAX_FILE_BYTES}",
            )
        if entrada.tamanho_comprimido != entrada.tamanho:
            raise recusa("size_inconsistent", entrada.nome)
        total += entrada.tamanho
    if total > MAX_CONTENT_BYTES:
        raise FalhaDoWorker(
            EXIT_PACOTE_INVALIDO, f"o conteúdo soma {total} bytes; o limite é {MAX_CONTENT_BYTES}"
        )
    return arquivos, destino


def modo_do_arquivo(nome: str) -> int:
    """Permissão do arquivo instalado: a do processo, nunca a do zip; `hook.sh` executa (seção 10.2)."""
    return 0o755 if nome.endswith("hook.sh") else 0o644


def registrar_skill(texto: str, tipo: str, nome: str, versao: str) -> str:
    """Devolve o `SKILL.md` com `amflow-source` e `amflow-status: published` no bloco `metadata`,
    sobrescrevendo o que vier no pacote (seção 10.2). Levanta `ValueError` se o frontmatter não
    permite a edição — a falha vira código 13 e a troca é desfeita."""
    fim_de_linha = "\r\n" if "\r\n" in texto else "\n"
    linhas = texto.split(fim_de_linha)
    if not linhas or linhas[0].strip() != "---":
        raise ValueError("SKILL.md sem frontmatter")
    try:
        fechamento = next(i for i in range(1, len(linhas)) if linhas[i].strip() == "---")
    except StopIteration:
        raise ValueError("frontmatter do SKILL.md não fecha") from None

    registro = {"amflow-source": f"hub/{tipo}/{nome}@{versao}", "amflow-status": "published"}
    corpo = linhas[1:fechamento]
    inicio = next((i for i, linha in enumerate(corpo) if re.fullmatch(r"metadata:\s*(\{\s*\})?\s*", linha)), None)
    if inicio is None and any(re.match(r"metadata:\s*\S", linha) for linha in corpo):
        raise ValueError("`metadata` do SKILL.md não é um bloco")

    if inicio is None:
        novo = corpo + ["metadata:"] + [f"  {chave}: {valor}" for chave, valor in registro.items()]
        return fim_de_linha.join([linhas[0]] + novo + linhas[fechamento:])

    fim_bloco = inicio + 1
    while fim_bloco < len(corpo) and (corpo[fim_bloco].startswith((" ", "\t")) or not corpo[fim_bloco].strip()):
        fim_bloco += 1
    while fim_bloco > inicio + 1 and not corpo[fim_bloco - 1].strip():
        fim_bloco -= 1
    filhos = corpo[inicio + 1 : fim_bloco]
    recuo = next((re.match(r"\s*", f).group(0) for f in filhos if f.strip()), "  ")
    filhos = [f for f in filhos if not re.match(rf"{re.escape(recuo)}(amflow-source|amflow-status)\s*:", f)]
    filhos += [f"{recuo}{chave}: {valor}" for chave, valor in registro.items()]
    novo = corpo[:inicio] + ["metadata:"] + filhos + corpo[fim_bloco:]
    return fim_de_linha.join([linhas[0]] + novo + linhas[fechamento:])

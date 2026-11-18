"""`fetch_package_app.py` — o caso de uso do recebimento: duas fases, com a M10 entre elas.

Não toca disco nem rede: o `disco` chega por argumento (norma `clean-architecture.md`, seção 5). Cada
função devolve `(código de saída, linhas de saída)`. Seções 9.4 a 10.3 do index.md do plano 0028.
"""

from __future__ import annotations

from fetch_package_domain import (
    EXIT_DESTINO,
    EXIT_OK,
    EXIT_PACOTE_INVALIDO,
    EXIT_SEM_EGRESS,
    EXIT_TRANSPORTE,
    EXIT_USO,
    FalhaDoWorker,
    FalhaTransporte,
    SemEgress,
    candidatos_do_destino,
    conferir_download,
    inspecionar_entradas,
    interpretar_itens,
    interpretar_registros,
    modo_do_arquivo,
    registrar_skill,
)

_PREFIXO_CLAUDE = ".claude/"


def _erro(falha: FalhaDoWorker) -> tuple[int, list[str]]:
    return falha.codigo, ["RESULTADO: ERRO", f"MOTIVO: {falha.motivo}"]


def restaurar_reservas(disco, raiz: str) -> None:
    """Interrompido o script, a execução seguinte encontra a reserva: destino ausente → restaura;
    presente → apaga (seção 10.3). Sem arquivo de estado: o próprio disco diz o que houve."""
    try:
        _restaurar(disco, raiz)
    except OSError as exc:
        raise FalhaDoWorker(EXIT_DESTINO, f"não foi possível restaurar a reserva de uma execução interrompida — {exc}")


def _restaurar(disco, raiz: str) -> None:
    base = disco.juntar(raiz, ".claude", ".amflow-reserva")
    for pasta in disco.listar(base):
        if not pasta.endswith("s") or pasta[:-1] not in ("skill", "agent", "command", "hook"):
            continue
        tipo = pasta[:-1]
        grupos: dict[str, list[str]] = {}
        for entrada in disco.listar(disco.juntar(base, pasta)):
            nome = entrada[:-3] if tipo in ("agent", "command") and entrada.endswith(".md") else entrada
            grupos.setdefault(nome, []).append(entrada)
        for nome, entradas in grupos.items():
            candidatos = candidatos_do_destino(tipo, nome)
            ocupado = any(disco.existe(disco.juntar(raiz, c)) for c in candidatos)
            for entrada in entradas:
                reservado = disco.juntar(base, pasta, entrada)
                if ocupado:
                    disco.apagar(reservado)
                else:
                    disco.mover(reservado, disco.juntar(raiz, ".claude", pasta, entrada))
    disco.remover_se_vazio(base)


def baixar(bruto, raiz: str, disco) -> tuple[int, list[str]]:
    """Fase 1: baixa, confere tamanho e SHA-256, inspeciona os nomes e grava `pacotes.json`. Em
    qualquer falha apaga a `<area>` e devolve o código da classe."""
    try:
        itens = interpretar_itens(bruto)
        restaurar_reservas(disco, raiz)
        area = disco.criar_area(raiz)
    except FalhaDoWorker as falha:
        return _erro(falha)

    linhas = [f"AREA: {area}"]
    registros = []
    try:
        for posicao, item in enumerate(itens):
            nome_zip = f"{posicao}.zip"
            try:
                tamanho, sha256 = disco.baixar(item.download_url, area, nome_zip, item.tamanho)
            except SemEgress as exc:
                raise FalhaDoWorker(EXIT_SEM_EGRESS, f"sem conexão com o domínio do link — {exc}")
            except FalhaTransporte as exc:
                raise FalhaDoWorker(EXIT_TRANSPORTE, f"falha de transporte — {exc}")
            conferir_download(item, tamanho, sha256)
            arquivos, _ = inspecionar_entradas(item.tipo, item.nome, disco.ler_entradas(area, nome_zip))
            if len(arquivos) != item.arquivos:
                raise FalhaDoWorker(
                    EXIT_PACOTE_INVALIDO,
                    f"`{item.tipo}/{item.nome}`: {len(arquivos)} arquivos no pacote, o Hub declarou {item.arquivos}",
                )
            linhas.append(
                f"PACOTE: {item.role} {item.tipo}/{item.nome}@{item.versao} "
                f"arquivos={len(arquivos)} bytes={sum(e.tamanho for e in arquivos)}"
            )
            linhas.extend(f"ARQUIVO: {e.nome} {e.tamanho}" for e in arquivos)
            registros.append(
                {
                    "role": item.role,
                    "type": item.tipo,
                    "name": item.nome,
                    "version": item.versao,
                    "zip": nome_zip,
                    "sha256": item.sha256,
                    "size_bytes": item.tamanho,
                    "file_count": item.arquivos,
                }
            )
        disco.gravar_pacotes(area, registros)
    except FalhaDoWorker as falha:
        disco.apagar_area(raiz, area)
        return _erro(falha)
    linhas.append("RESULTADO: OK")
    return EXIT_OK, linhas


def trocar(disco, raiz: str, area: str, tipo: str, nome: str, versao: str, destino: str) -> None:
    """Troca por recurso, tudo ou nada (seção 10.3): a versão antiga vai para a reserva, a nova assume o
    lugar, o registro local é gravado depois, e só então a reserva é apagada. Duas renomeações, com
    desfazer — `os.replace` não substitui diretório não vazio."""
    disco.verificar_destino(raiz, destino)
    reserva = disco.juntar(raiz, ".claude", ".amflow-reserva")
    novo = disco.juntar(area, "extraido", destino)
    alvo = disco.juntar(raiz, destino)

    movidos: list[tuple[str, str]] = []

    def desfazer() -> None:
        # Volta na ordem inversa. Se o desfazer também falha, a reserva fica onde está e a próxima
        # execução a restaura (restaurar_reservas); o motivo diz onde.
        try:
            for origem, guardado in reversed(movidos):
                disco.mover(guardado, origem)
        except OSError as exc:
            raise FalhaDoWorker(
                EXIT_DESTINO,
                f"a troca falhou e o desfazer também; a versão anterior está em `{reserva}` "
                f"e a próxima execução a restaura — {exc}",
            )

    try:
        for candidato in candidatos_do_destino(tipo, nome):
            atual = disco.juntar(raiz, candidato)
            if disco.existe(atual):
                guardado = disco.juntar(reserva, candidato[len(_PREFIXO_CLAUDE):])
                disco.mover(atual, guardado)
                movidos.append((atual, guardado))
        disco.mover(novo, alvo)
    except OSError as exc:
        desfazer()
        raise FalhaDoWorker(EXIT_DESTINO, f"a troca de `{tipo}/{nome}` falhou e foi desfeita — {exc}")

    if tipo == "skill":
        manifesto = disco.juntar(alvo, "SKILL.md")
        try:
            disco.escrever_texto(manifesto, registrar_skill(disco.ler_texto(manifesto), tipo, nome, versao))
        except (OSError, ValueError) as exc:
            try:
                disco.mover(alvo, novo)
            except OSError as exc_mover:
                raise FalhaDoWorker(EXIT_DESTINO, f"o registro local falhou e a troca não pôde ser desfeita — {exc_mover}")
            desfazer()
            raise FalhaDoWorker(EXIT_DESTINO, f"o registro local de `{tipo}/{nome}` falhou e a troca foi desfeita — {exc}")

    for _, guardado in movidos:
        disco.apagar(guardado)


def aplicar(raiz: str, area: str, disco) -> tuple[int, list[str]]:
    """Fase 2: refaz a conferência de SHA-256, extrai e troca recurso por recurso. Falha num recurso
    não impede o próximo; o código de saída é o do primeiro que falhou. Apaga a `<area>` ao fim."""
    try:
        disco.validar_area(raiz, area)
        restaurar_reservas(disco, raiz)
        registros = interpretar_registros(disco.ler_pacotes(area))
        # O tempo entre as fases é o da M10: o que está na área pode ter mudado.
        for registro in registros:
            tamanho, sha256 = disco.hash_arquivo(area, registro.zip)
            conferir_download(registro, tamanho, sha256)
    except FalhaDoWorker as falha:
        if falha.codigo != EXIT_USO:
            disco.apagar_area(raiz, area)
        return _erro(falha)

    linhas: list[str] = []
    primeiro = EXIT_OK
    for registro in registros:
        rotulo = f"{registro.tipo}/{registro.nome}"
        try:
            arquivos, destino = inspecionar_entradas(
                registro.tipo, registro.nome, disco.ler_entradas(area, registro.zip)
            )
            disco.extrair(area, registro.zip, arquivos, modo_do_arquivo)
            trocar(disco, raiz, area, registro.tipo, registro.nome, registro.versao, destino)
        except FalhaDoWorker as falha:
            primeiro = primeiro or falha.codigo
            linhas += ["RESULTADO: ERRO", f"MOTIVO: {rotulo}: {falha.motivo}"]
            continue
        linhas.append(f"INSTALADO: {rotulo}@{registro.versao}")
    disco.apagar_area(raiz, area)
    if primeiro == EXIT_OK:
        linhas.append("RESULTADO: OK")
    return primeiro, linhas


def descartar(raiz: str, area: str, disco) -> tuple[int, list[str]]:
    """Cancelamento na M10: apaga a `<area>` sem instalar nada. Só apaga o que `validar_area` aceita —
    filha direta de `<raiz>/.claude/.amflow-tmp/` depois de resolvido o caminho; qualquer outra coisa é
    recusada com código 2 e nada é apagado."""
    try:
        disco.validar_area(raiz, area)
    except FalhaDoWorker as falha:
        return _erro(falha)
    disco.apagar_area(raiz, area)
    return EXIT_OK, ["RESULTADO: OK"]

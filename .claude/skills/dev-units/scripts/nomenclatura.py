#!/usr/bin/env python3
"""Validação sintática de nome e colisão no alvo — unidade 0002-03.

Metade determinística da regra de nomes (norma, decisão 20): a skill sugere um
nome com julgamento semântico, este módulo valida a sintaxe e a colisão no
alvo. Toda recusa vem com o motivo — nunca só o primeiro — para que a skill
corrija sem precisar adivinhar qual regra falhou.

"Sem repetir o caminho" fica de fora deliberadamente: só quem conhece o alvo
sabe se um token repete o caminho, e essa metade semântica pertence à skill,
não a este script.
"""

from __future__ import annotations

import re
from pathlib import Path

import lib

CONECTIVOS = {"e", "de", "para", "do", "da"}


def validar_nome(nome: str) -> list[str]:
    """Valida a sintaxe de um nome de plano ou unidade.

    Devolve a lista de motivos da recusa — vazia quando o nome é válido. As
    seis regras são checadas de forma independente: um nome pode acumular
    mais de um motivo na mesma chamada. Nunca levanta por nome inválido.
    """
    motivos: list[str] = []

    invalidos = sorted(set(re.findall(r"[^a-z0-9-]", nome)))
    if invalidos:
        lista = ", ".join(repr(c) for c in invalidos)
        motivos.append(
            f"contém caractere(s) fora de minúsculas, dígitos e hífen — {lista}"
        )

    bordas = []
    if nome.startswith("-"):
        bordas.append("hífen inicial")
    if nome.endswith("-"):
        bordas.append("hífen final")
    if "--" in nome:
        bordas.append("hífen consecutivo")
    if bordas:
        motivos.append(f"tem {', '.join(bordas)}")

    if len(nome) > 64:
        motivos.append(f"tem {len(nome)} caracteres — máximo é 64")

    tokens = nome.split("-")
    if not 2 <= len(tokens) <= 5:
        motivos.append(
            f"tem {len(tokens)} token(s) separado(s) por hífen — precisa de 2 a 5"
        )

    isolados = [t for t in tokens if t in CONECTIVOS]
    if isolados:
        motivos.append(f"tem conectivo isolado como token — {', '.join(isolados)}")

    if tokens and tokens[0].isdigit():
        motivos.append(
            f"começa com prefixo numérico {tokens[0]!r} — o número é atribuído "
            "na aprovação, nunca escrito à mão"
        )

    return motivos


def _sem_prefixo_numerico(nome: str) -> str:
    """Remove um prefixo `NNNN-` ou `NN-` — o número é atribuído na aprovação, nunca escrito no nome."""
    return re.sub(r"^\d+-", "", nome)


def _colisao_em(pasta: Path, nome: str) -> Path | None:
    """Primeiro item de `pasta` cujo nome — sem extensão nos arquivos, sem
    prefixo numérico — é igual a `nome`. None se a pasta não existir ou nada colidir.
    """
    if not pasta.is_dir():
        return None
    for item in sorted(pasta.iterdir()):
        chave = item.stem if item.is_file() else item.name
        if _sem_prefixo_numerico(chave) == nome:
            return item
    return None


def ha_colisao(nome: str, core: str, module: str | None = None) -> Path | None:
    """Varre o alvo por um nome já em uso — o caminho colidente, ou None.

    Sem `module`, colide como nome de **plano**: um arquivo já proposto em
    `_inbox/` (nome semântico, sem prefixo) ou uma pasta de módulo já
    aprovada em `core_dir(core)` (`0001-mcp` → `mcp`). Com `module`, colide
    como nome de **unidade**: um arquivo já existente dentro da pasta desse
    módulo (`01-handler-auth.md` → `handler-auth`).

    Levanta `ValueError` se `core` não existir em disco — único caso em que
    este módulo levanta.
    """
    alvo_core = lib.core_dir(core)
    if not alvo_core.is_dir():
        raise ValueError(f"core {core!r} não existe em {alvo_core}")

    if module is None:
        return _colisao_em(lib.inbox(), nome) or _colisao_em(alvo_core, nome)

    pasta_modulo = _colisao_em(alvo_core, module)
    if pasta_modulo is None:
        return None
    return _colisao_em(pasta_modulo, nome)

#!/usr/bin/env python3
"""Leitura e escrita de regiões delimitadas de um markdown — unidade 0002-02.

Expõe dois pares de operação sobre um arquivo `.md`: campos nomeados do
frontmatter (`chave: valor`, uma linha cada) e blocos delimitados por
marcadores de comentário (`<!-- marcador:start -->` … `<!-- marcador:end -->`).
Fora dessas regiões, o script nunca toca o arquivo — é o invariante que dá
nome à unidade (norma, decisão 13).

Sem parsing de YAML (decisão D-01 do plano): cada campo é casado por regex de
linha, e escrever um campo substitui a linha inteira por `chave: valor`, sem
tentar preservar um comentário à direita que porventura exista na linha
original. A alternativa — separar valor de comentário sem um parser de
verdade — reintroduziria a mesma classe de bug que a decisão D-01 rejeita ao
descartar `pyyaml`: heurística que acerta o caso comum e corrompe o raro.
Nenhum campo hoje escrito por este módulo (`state`, `test`, `verified_at`)
carrega comentário inline nas instâncias reais do repositório.
"""

from __future__ import annotations

import re
from pathlib import Path


def _linhas_com_quebra(path: Path) -> list[str]:
    """Lê o arquivo linha a linha, preservando a quebra de linha original de cada uma."""
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def _sem_quebra(linha: str) -> str:
    """Conteúdo da linha sem o terminador (`\\n` ou `\\r\\n`)."""
    return linha.rstrip("\r\n")


def _limites_frontmatter(linhas: list[str], path: Path) -> tuple[int, int]:
    """Índice da linha de abertura (sempre 0) e da linha de fechamento do frontmatter.

    As duas precisam ser `---` isolado. Sem as duas, o arquivo não tem
    frontmatter válido.
    """
    if not linhas or _sem_quebra(linhas[0]) != "---":
        raise ValueError(f"{path} não começa com frontmatter '---'")
    for i in range(1, len(linhas)):
        if _sem_quebra(linhas[i]) == "---":
            return 0, i
    raise ValueError(f"{path} tem frontmatter aberto mas sem '---' de fechamento")


def ler_campo(path: Path, chave: str) -> str | None:
    """Lê o valor de um campo do frontmatter — None se o campo não existir.

    Casa apenas `^chave:\\s*(.*)$` dentro da região do frontmatter, sem
    interpretar o valor como YAML.
    """
    linhas = _linhas_com_quebra(path)
    inicio, fim = _limites_frontmatter(linhas, path)

    padrao = re.compile(rf"^{re.escape(chave)}:\s*(.*)$")
    for linha in linhas[inicio + 1 : fim]:
        m = padrao.match(_sem_quebra(linha))
        if m:
            return m.group(1)
    return None


def escrever_campos(path: Path, campos: dict[str, str]) -> bool:
    """Escreve um ou mais campos do frontmatter, cada um substituindo só a própria linha.

    Recusa com `ValueError` — sem gravar nada — se algum campo não existir:
    acrescentar campo é decisão humana, não do script. Só grava se o
    resultado for diferente do conteúdo atual; devolve se gravou.
    """
    linhas = _linhas_com_quebra(path)
    inicio, fim = _limites_frontmatter(linhas, path)

    indice_da_chave: dict[str, int] = {}
    for chave in campos:
        padrao = re.compile(rf"^{re.escape(chave)}:\s*(.*)$")
        encontrado = None
        for i in range(inicio + 1, fim):
            if padrao.match(_sem_quebra(linhas[i])):
                encontrado = i
                break
        if encontrado is None:
            raise ValueError(f"campo {chave!r} não existe no frontmatter de {path}")
        indice_da_chave[chave] = encontrado

    novas_linhas = list(linhas)
    for chave, valor in campos.items():
        i = indice_da_chave[chave]
        quebra = linhas[i][len(_sem_quebra(linhas[i])) :]
        novas_linhas[i] = f"{chave}: {valor}{quebra}"

    texto_original = "".join(linhas)
    texto_novo = "".join(novas_linhas)
    if texto_novo == texto_original:
        return False
    path.write_text(texto_novo, encoding="utf-8")
    return True


def _marcadores(marcador: str) -> tuple[str, str]:
    return f"<!-- {marcador}:start -->", f"<!-- {marcador}:end -->"


def _localizar_regiao(texto: str, marcador: str, path: Path) -> tuple[int, int] | None:
    """Posições `(inicio, fim)` do miolo entre os marcadores — None se o marcador não existir.

    "Não existir" é o par inteiro ausente — região que este documento
    legitimamente não tem. Só um dos dois marcadores presente é documento
    quebrado: `ValueError`, não None.
    """
    tag_inicio, tag_fim = _marcadores(marcador)
    i_inicio = texto.find(tag_inicio)
    i_fim = texto.find(tag_fim)

    if i_inicio == -1 and i_fim == -1:
        return None
    if i_inicio == -1 or i_fim == -1:
        raise ValueError(f"marcador {marcador!r} sem par em {path}")
    if i_fim < i_inicio:
        raise ValueError(f"marcador {marcador!r} com 'end' antes de 'start' em {path}")

    return i_inicio + len(tag_inicio), i_fim


def ler_regiao(path: Path, marcador: str) -> str | None:
    """Lê o miolo entre `<!-- marcador:start -->` e `<!-- marcador:end -->`.

    None se o marcador não existir no documento; `ValueError` se o par
    estiver incompleto.
    """
    texto = path.read_text(encoding="utf-8")
    limites = _localizar_regiao(texto, marcador, path)
    if limites is None:
        return None
    inicio, fim = limites
    return texto[inicio:fim]


def escrever_regiao(path: Path, marcador: str, conteudo: str) -> bool:
    """Substitui o miolo entre os marcadores, preservando as linhas dos marcadores.

    Recusa com `ValueError` — sem gravar nada — se o par não existir: região
    nova é decisão humana, não do script. Só grava se o resultado for
    diferente do conteúdo atual; devolve se gravou.
    """
    texto_original = path.read_text(encoding="utf-8")
    limites = _localizar_regiao(texto_original, marcador, path)
    if limites is None:
        raise ValueError(f"marcador {marcador!r} não existe em {path}")
    inicio, fim = limites

    texto_novo = texto_original[:inicio] + conteudo + texto_original[fim:]
    if texto_novo == texto_original:
        return False
    path.write_text(texto_novo, encoding="utf-8")
    return True

#!/usr/bin/env python3
"""Projeção de backlog e de situação — unidade 0002-09.

Duas superfícies derivadas de uma fonte única: o estado real vive no frontmatter de cada unidade
(`unit_id`, `state`, título). Este módulo projeta o backlog no arquivo do plano — o miolo entre
`<!-- backlog:start -->`/`<!-- backlog:end -->` — e a coluna Situação da linha do plano em
`_planos.md`. Por serem derivadas de uma leitura só do disco, as duas nunca divergem entre si; e
`regioes.escrever_regiao` só grava se o resultado mudou, o que dá a idempotência que o critério de
aceite exige (norma, decisão 17 e "Estado derivado de verificação").

Tudo é validado antes de qualquer escrita: plano sem os marcadores do backlog, ou sem linha
correspondente em `_planos.md`, levanta `ValueError` sem tocar em nenhum dos dois arquivos — inclusive
em `dry_run`, que nunca grava.

Sobre "X de Y derivadas" (D-03). Esta implementação computa X e Y do mesmo conjunto — as unidades
achadas em disco —, exatamente como a Sequência da unidade descreve: ela só manda listar `NN-*.md`,
nunca ler o corpo do plano além do próprio backlog. Por isso "X de Y derivadas" sai sempre "N de N":
todo arquivo achado já é, por definição, derivado. Uma leitura alternativa é sugerida pelo exemplo
real em `docs/plan/hub/0001-mcp/0001-mcp.md` ("1 de 10 derivadas", contra as dez linhas da sua seção
Escopo e a única unidade hoje em disco) e pela própria razão de D-03 ("carrega informação que a norma
omite") — ali "Y" seria o total *planejado*, não o já derivado. Não foi implementada: exigiria
parsear uma tabela sob heading de nível 2 (possivelmente mais de uma, como no próprio 0002-dev-units,
com Fase 1 e Fase 2 em tabelas separadas) — exatamente a fragilidade que este documento rejeita para
o próprio backlog ("parsear heading é frágil... Região delimitada não tem esse risco") — e a
Sequência da unidade não declara esse passo. Fica registrado como leitura pendente de confirmação,
não como lacuna silenciosa.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import NamedTuple

import lib
import numeracao
import regioes

_H1 = re.compile(r"^#\s+(.+?)\s*$")


class _Unidade(NamedTuple):
    arquivo: Path
    unit_id: str | None
    state: str | None
    titulo: str | None


def projetar(dir_plano: Path, dry_run: bool = False) -> tuple[str, str]:
    """Projeta o backlog do plano e a situação derivada — devolve `(backlog, situacao)`.

    Levanta `ValueError` se o plano não tem os marcadores `backlog:start`/`backlog:end`, ou se não
    tem linha correspondente em `_planos.md`. As duas checagens rodam antes de qualquer escrita.

    O caminho é resolvido na entrada: `lib.plan_root()` já vem resolvido, e `relative_to` entre um
    caminho resolvido e outro não quebra com `ValueError` obscuro — foi o que aconteceu ao chamar com
    caminho relativo em 2026-07-26. É o mesmo cuidado que a unidade 0002-01 fixou e que o `move-md`
    aprendeu com symlink.
    """
    dir_plano = Path(dir_plano).resolve()
    arquivo_do_plano = dir_plano / f"{dir_plano.name}.md"

    if regioes.ler_regiao(arquivo_do_plano, "backlog") is None:
        raise ValueError(f"marcador 'backlog' não existe em {arquivo_do_plano}")

    href = arquivo_do_plano.relative_to(lib.plan_root()).as_posix()
    miolo_planos = regioes.ler_regiao(lib.planos_md(), "planos")
    if miolo_planos is None:
        raise ValueError(f"região 'planos' ausente em {lib.planos_md()}")
    if f"]({href})" not in miolo_planos:
        raise ValueError(f"plano {href!r} não tem linha em {lib.planos_md()}")

    unidades = sorted(_unidades(dir_plano), key=_chave_ordenacao)
    backlog = _montar_backlog(unidades)
    situacao = _situacao(unidades)

    if dry_run:
        return backlog, situacao

    regioes.escrever_regiao(arquivo_do_plano, "backlog", backlog)
    regioes.escrever_regiao(lib.planos_md(), "planos", _substituir_situacao(miolo_planos, href, situacao))

    return backlog, situacao


def _unidades(dir_plano: Path) -> list[_Unidade]:
    """Lê `unit_id`, `state` e título de cada `NN-*.md` do diretório — nunca o arquivo do plano."""
    arquivo_do_plano = f"{dir_plano.name}.md"
    unidades = []
    for item in dir_plano.iterdir():
        if not item.is_file() or item.name == arquivo_do_plano:
            continue
        if not numeracao.PADRAO_ARQUIVO_UNIDADE.match(item.name):
            continue
        unit_id = regioes.ler_campo(item, "unit_id")
        state = regioes.ler_campo(item, "state")
        unidades.append(_Unidade(item, unit_id, state, _titulo(item, unit_id)))
    return unidades


def _chave_ordenacao(unidade: _Unidade) -> tuple[bool, str, str]:
    """Por `unit_id` — nunca pela ordem do sistema de arquivos, que varia por plataforma.

    `unit_id` ausente ordena por último, pelo nome do arquivo — nunca quebra a ordenação inteira.
    """
    return (unidade.unit_id is None, unidade.unit_id or "", unidade.arquivo.name)


def _primeiro_h1(path: Path) -> str | None:
    """Primeiro `# título` do corpo — nunca da região de frontmatter, que também começa com `#`."""
    linhas = path.read_text(encoding="utf-8").splitlines()
    if not linhas or linhas[0].strip() != "---":
        return None

    fim = None
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            fim = i
            break
    if fim is None:
        return None

    for linha in linhas[fim + 1 :]:
        m = _H1.match(linha)
        if m:
            return m.group(1)
    return None


def _titulo(path: Path, unit_id: str | None) -> str | None:
    """Título do H1, sem o prefixo `unit_id — `.

    O prefixo é reconhecido pelo `unit_id` já lido do frontmatter — nunca por um padrão genérico de
    dígitos — para que um H1 fora da convenção não tenha texto cortado por engano.
    """
    bruto = _primeiro_h1(path)
    if bruto is None:
        return None
    prefixo = f"{unit_id} — "
    if unit_id and bruto.startswith(prefixo):
        return bruto[len(prefixo) :]
    return bruto


def _linha_unidade(unidade: _Unidade) -> str:
    """Uma linha da tabela — unidade sem título entra como problema visível, nunca como exceção."""
    texto_link = unidade.unit_id or unidade.arquivo.stem
    titulo = unidade.titulo or "(sem título)"
    estado = f"`{unidade.state}`" if unidade.state else "—"
    return f"| [{texto_link}]({unidade.arquivo.name}) | {titulo} | {estado} |"


def _plural(quantidade: int, singular: str, plural: str) -> str:
    return singular if quantidade == 1 else plural


def _montar_rodape(unidades: list[_Unidade]) -> str:
    total = len(unidades)
    verificadas = sum(1 for u in unidades if u.state == "verified")
    hoje = date.today().isoformat()
    return (
        f"{total} de {total} {_plural(total, 'derivada', 'derivadas')} · "
        f"{verificadas} {_plural(verificadas, 'verificada', 'verificadas')} · "
        f"atualizado em {hoje}"
    )


def _montar_backlog(unidades: list[_Unidade]) -> str:
    """O miolo completo da região `backlog` — tabela, linha em branco e rodapé."""
    linhas = ["", "| Unidade | Título | Estado |", "|---|---|---|"]
    linhas += [_linha_unidade(u) for u in unidades]
    linhas += ["", _montar_rodape(unidades)]
    return "\n".join(linhas) + "\n"


def _situacao(unidades: list[_Unidade]) -> str:
    """`concluído` só com unidades e todas `verified`; lista vazia nunca conta como concluída."""
    if unidades and all(u.state == "verified" for u in unidades):
        return "concluído"
    return "em desenvolvimento"


def _substituir_situacao(miolo: str, href: str, nova_situacao: str) -> str:
    """Troca só a coluna Situação da linha que linka para `href` — as demais, inclusive Origem, ficam como estão."""
    alvo = f"]({href})"
    linhas = miolo.split("\n")
    for i, linha in enumerate(linhas):
        if alvo in linha:
            linhas[i] = _substituir_coluna(linha, nova_situacao)
            return "\n".join(linhas)
    raise ValueError(f"nenhuma linha contém {alvo!r}")


def _substituir_coluna(linha: str, nova_situacao: str) -> str:
    partes = linha.split("|")
    if len(partes) != 9:
        raise ValueError(f"linha de _planos.md não tem 7 colunas — {linha!r}")
    partes[6] = f" {nova_situacao} "
    return "|".join(partes)

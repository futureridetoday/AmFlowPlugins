#!/usr/bin/env python3
"""Scaffold da aprovação de um plano — unidade 0002-05.

Transforma um plano aprovado no `_inbox` em estrutura permanente numa operação só: monta o alvo
`<core>/<NNNN>-<nome>/<NNNN>-<nome>.md`, delega a movimentação a `scripts/move-md.py` — que já
reescreve os links nas duas direções, resolve symlink e ignora bloco de código — e registra
`plan_id`/`status` no plano e a linha correspondente em `_planos.md` (norma, decisão D-04 do plano).

Move primeiro, escreve o frontmatter depois: se a movimentação falhar, o plano continua íntegro no
`_inbox` e a operação é retomável; o inverso deixaria um plano marcado como aprovado sem nunca ter
saído do lugar.

`scripts/move-md.py` tem hífen no nome do arquivo — não é importável por `import` direto. É
carregado por `importlib.util`, como o próprio teste do move-md já faz, para que `REPO_ROOT`
continue substituível por mock nos testes desta unidade também.

O `<nome>` do alvo é o nome do próprio arquivo do plano (decisão 19 — o plano mantém o nome ao sair
do `_inbox`), não o campo `module` do frontmatter: os dois costumam coincidir quando o plano cria o
módulo, mas nada garante que sejam o mesmo valor.

`block` não é lido: a fórmula do alvo desta unidade usa só `core` e `<nome>`. A norma prevê bloco
como pasta numerada dentro do módulo (`hub/0001-mcp/0005-oauth/`), forma que exigiria outro alvo —
plano que cria bloco fica fora do que esta unidade cobre (lacuna L-08 do plano).
"""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import lib
import nomenclatura
import numeracao
import regioes

_spec = importlib.util.spec_from_file_location(
    "move_md", lib.repo_root() / "scripts" / "move-md.py"
)
move_md = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(move_md)


def _campo_vazio(valor: str | None) -> bool:
    """True se o campo está ausente ou sem valor real.

    Inclui o padrão `""` que o repositório usa para campo vazio no frontmatter (ex.: `block: ""`
    em `0002-dev-units.md`) — sem isso, um `core: ""` não preenchido passaria como valor válido,
    porque `ler_campo` nunca interpreta o texto como YAML (decisão D-01).
    """
    if valor is None:
        return True
    return valor.strip(" \t\"'") == ""


def _mover(origem: Path, destino: Path) -> None:
    """Move o plano compondo move-md — nunca reimplementando a reescrita de links."""
    conteudo = origem.read_text(encoding="utf-8")
    novo_conteudo, _ = move_md.reescrever_links_internos(conteudo, origem.parent, destino.parent)
    move_md.mover(origem, destino)
    destino.write_text(novo_conteudo, encoding="utf-8")
    move_md.reescrever_referencias(origem, destino, dry_run=False)


def _linha_planos_md(numero: str, nome: str, core: str, module: str | None, alvo: Path) -> str:
    href = alvo.relative_to(lib.plan_root()).as_posix()
    hoje = date.today().isoformat()
    return (
        f"| {numero} | [{nome}]({href}) | {core} | {module or ''} | — | "
        f"em desenvolvimento | {hoje} |\n"
    )


def _registrar_planos_md(
    numero: str, nome: str, core: str, module: str | None, alvo: Path
) -> None:
    caminho = lib.planos_md()
    miolo = regioes.ler_regiao(caminho, "planos")
    linha = _linha_planos_md(numero, nome, core, module, alvo)
    regioes.escrever_regiao(caminho, "planos", (miolo or "") + linha)


def aprovar(plano: Path, dry_run: bool = False) -> Path:
    """Aprova um plano do `_inbox` — devolve o caminho final, movido ou só calculado em dry-run.

    Levanta `ValueError` se o plano não declara `core`, ou se o nome do arquivo falha a validação
    sintática (`nomenclatura.validar_nome`). Levanta `FileExistsError` se o alvo já existe. Em
    qualquer um dos dois casos — inclusive em `dry_run` — nada é escrito.
    """
    core = regioes.ler_campo(plano, "core")
    if _campo_vazio(core):
        raise ValueError(f"plano não declara 'core' — {plano}")

    module = regioes.ler_campo(plano, "module")

    numero = numeracao.proximo_plano()
    nome = plano.stem
    motivos = nomenclatura.validar_nome(nome)
    if motivos:
        raise ValueError(f"nome de plano inválido {nome!r} — {'; '.join(motivos)}")

    alvo = lib.core_dir(core) / f"{numero}-{nome}" / f"{numero}-{nome}.md"
    if alvo.exists():
        raise FileExistsError(f"alvo já existe — {alvo}")

    if dry_run:
        return alvo

    _mover(plano, alvo)
    regioes.escrever_campos(alvo, {"plan_id": f'"{numero}"', "status": "approved"})
    _registrar_planos_md(numero, nome, core, module, alvo)

    return alvo

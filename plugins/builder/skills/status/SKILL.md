---
name: status
description: |
  Lista e atualiza o status dos recursos do projeto do Creator: mostra o que está em andamento,
  pausado, bloqueado, pronto para publicar, em revisão, com ajustes pedidos, recusado ou publicado,
  filtra por status e marca um recurso como pausado, bloqueado, retomado, pronto ou descontinuado. Use
  when o Creator quer saber o que está pendente para concluir, buscar recursos por status ou mudar o
  status de um recurso.
license: Proprietary
metadata:
  amflow-version: "1.0.0"
  amflow-status: in_progress
  amflow-author: Bortoli
  amflow-author-id: 985920db-502d-4cb3-9ca1-c145719a9307
  amflow-updated: "2026-09-12"
  amflow-tags: creator status metadata resource-status builder
  amflow-dependencies: ""
---

# Status

Lista, filtra e atualiza o campo `metadata.amflow-status` dos recursos do Creator — skill, agent,
command, hook e módulo. Todo determinismo — varredura, leitura, validação, ordenação, escrita — é do
`status.py`; esta skill só interpreta o pedido em linguagem natural e chama o script.

## Quando usar

- "o que eu tenho pendente para terminar neste projeto?"
- "quais recursos estão prontos para publicar?"
- "marca a skill deep-research como bloqueada, esperando a API de licenças"
- "retoma o agent reviewer" / "pausa o command publish-status"

## Quando não usar

- "qual o status do git?" — é do Claude Code, não deste plugin. "Status" sozinho é o maior risco de
  falso positivo aqui
- "publica a skill deep-research" — é `/amflow-builder:publish`
- "o Hub já respondeu sobre a submissão da deep-research?" — é `/amflow-builder:publish-status`, que
  consulta o Hub; esta skill nunca faz rede

## O domínio

| Valor | Rótulo | Quem grava |
|---|---|---|
| `in_progress` | Em andamento | template na criação; Creator, ao retomar |
| `paused` | Pausado | Creator |
| `blocked` | Bloqueado, com motivo | Creator |
| `review` | Pronto para publicar | Creator |
| `deprecated` | Descontinuado | Creator |
| `pending_review` | Em revisão | `/amflow-builder:publish` |
| `changes_requested` | Ajustes pedidos | `/amflow-builder:publish-status` |
| `rejected` | Recusado | `/amflow-builder:publish-status` |
| `published` | Publicado | `/amflow-builder:publish-status` |

Os quatro últimos vêm do Hub — esta skill nunca os grava, só os exibe. Especificação completa:
`docs/plan/builder/0014-unify-status-field/index.md`, no repositório onde o Builder é desenvolvido.

## Processo

1. **Interpretar o pedido** — três formas:
   - **Listar / buscar por status**: sem alvo, ou com um rótulo da tabela acima. Traduzir o rótulo em
     pt-BR (ou a intenção do Creator) para o valor exato antes de filtrar — o script compara a string
     exata, e um valor errado devolve lista vazia em silêncio, não erro
   - **Atualizar**: o Creator nomeia um recurso e uma intenção — "pausa", "bloqueia", "retoma",
     "marca como pronto", "descontinua". Mapear a intenção para o valor exato da tabela; `blocked`
     sempre pede o motivo — perguntar se ele não veio junto do pedido
   - **Ambíguo**: recurso não identificado → listar os recursos do projeto e perguntar qual; valor
     não reconhecido → mostrar o domínio e perguntar de novo. Nunca adivinhar

2. **Resolver o projeto** — `$CLAUDE_PROJECT_DIR` quando definido; senão, o diretório de trabalho
   atual. É o `<projeto>` de todo comando abaixo.

3. **Chamar o script**, nunca reimplementar a lógica:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" list <projeto> [--status <valor>]
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" set <projeto> <tipo>/<nome> <valor> [--motivo <texto>]
   ```

   `<tipo>/<nome>` — ex.: `skill/deep-research`, `agent/reviewer`.

4. **Ler a saída, nunca reformular o julgamento do script**:

   | Saída | O que fazer |
   |---|---|
   | `list`, código 0 | Exibir as linhas tal como vieram, mais o total e o rodapé, se houver |
   | `list`, código 1 | Alguma linha começa com `ERRO` — um arquivo não parseou. Exibir o erro junto da lista; não escondê-lo |
   | `set`, código 0 | Exibir a mensagem de sucesso do script — ela já diz `de → para (arquivo)` |
   | `set`, código 1 | Exibir a mensagem de recusa tal como veio — nunca reformular. Cobre: valor do Hub, valor fora do domínio, `blocked` sem motivo, recurso não encontrado |

   Cada linha de `list` já vem pronta: `tipo | nome | local | status[, anotações] | rótulo`.
   `[Hub]` marca valor vindo do Hub; `[legado]` marca o recurso ainda no lugar antigo (`status` no
   topo, fora de `metadata`); `[fora do domínio]` marca valor que nenhuma das duas listas reconhece.
   Nenhuma dessas marcas se omite ao exibir.

5. **O rodapé, quando presente** — reproduzir literalmente:
   - `[Hub] reflete a última execução do /amflow-builder:publish-status — rode-o de novo para
     atualizar.` — aparece quando algum recurso listado tem valor de origem Hub
   - `Há recurso em revisão: rode /amflow-builder:publish-status para conferir.` — aparece quando
     algum recurso está em `pending_review`

   Nenhum dos dois é gerado por esta skill: são texto que o script devolve, e a única regra aqui é
   não cortá-los.

## Restrições

- **Nunca consultar o Hub.** Os quatro valores de origem Hub chegam ao arquivo pelo
  `/amflow-builder:publish-status`; esta skill só exibe o que já está gravado
- **Nunca gravar valor do Hub.** `set` recusa sozinho, mas a skill não deve nem tentar — se o pedido
  for "marca como publicado", explicar que isso é o Hub quem decide
- **Nunca reescrever em prosa o que o script decide** — domínio, ordem, formato, recusa. Se o
  comportamento parecer errado, o defeito é do script, não desta skill
- **`blocked` sempre com motivo.** Se o Creator não disser o motivo, perguntar antes de chamar `set`
- **Nunca apontar para o repositório AmFlow.** Ele é privado; o Creator não tem acesso

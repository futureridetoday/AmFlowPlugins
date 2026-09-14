---
# about
name: review
type: command
project: AmFlow
description: Lista os recursos do Creator em andamento e invoca o agent resource-reviewer sobre o escolhido — valida se está pronto para publicação, sem editar e sem publicar
tags: [review, quality, resource-reviewer, creator]

# history
author: Bortoli
created: 2026-09-13
status: draft
version: 1.0.0
updated: ""

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-builder:review

Lista os recursos do Creator com status `in_progress`, deixa escolher um, e invoca o agent
`resource-reviewer` sobre ele — devolve `APROVADO`/`REPROVADO`, sem editar o recurso e sem publicar.

## Quando usar

- "revisa a skill deep-research antes de eu publicar"
- "quais recursos estão prontos para eu revisar?"
- "valida esse agent antes de submeter"

## Quando não usar

- "publica a skill deep-research" — é `/amflow-builder:publish`
- "corrige o frontmatter da skill deep-research" — o `resource-reviewer` nunca edita, só reporta
- "qual o status da minha skill no Hub?" — é `/amflow-builder:publish-status`, que consulta o Hub;
  este comando nunca faz rede

## Processo

### Fase 1 — Listar recursos em andamento

1. Resolver o projeto — `$CLAUDE_PROJECT_DIR` quando definido; senão, o diretório de trabalho atual.
   É o `<projeto>` do comando abaixo.

2. Chamar o script, nunca reimplementar a varredura:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" list <projeto> --status in_progress
   ```

3. Ler a saída, nunca reformular o julgamento do script:

   | Saída | O que fazer |
   |---|---|
   | Código 0, com tabela | Reproduzir a tabela markdown tal como veio — cabeçalho e linhas |
   | Código 0, sem tabela (lista vazia) | Encerrar: **"Nenhum recurso em andamento encontrado."** |
   | Código 1 | Alguma linha começa com `ERRO` — exibir junto da tabela, não esconder |

### Fase 2 — Escolher o recurso

4. Perguntar ao Creator qual item da tabela revisar — por tipo/nome, ou pela linha. **Um recurso por
   execução**, nunca revisar a lista inteira em lote.

5. Item ambíguo ou fora da tabela → mostrar a tabela de novo e perguntar. Nunca adivinhar.

### Fase 3 — Invocar o resource-reviewer

6. Invocar o agent:

   ```
   Agent(resource-reviewer): "Revise o recurso <type>/<name> para publicação."
   ```

7. Reproduzir o relatório do `resource-reviewer` tal como veio — cabeçalho, `RESULTADO`, problemas
   bloqueantes e avisos. Nunca reformular o veredito nem resumir os problemas.

## Restrições

- Nunca editar o recurso — quem audita é o `resource-reviewer`, que também nunca edita.
- Nunca publicar nem chamar tool do servidor MCP `amflow-builder` — este comando é inteiramente local.
- Nunca consultar o Hub.
- Um recurso por execução — para revisar outro, executar de novo.

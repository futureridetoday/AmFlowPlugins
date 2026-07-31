---
# ── campos nativos do claude code ──────────────────────────────────────────────
name: workflow-name-workflow
description: |
  Orquestra o workflow workflow-name.
  Use when o usuário quer executar ou acompanhar o workflow workflow-name.

  <example>
  Context: workflow workflow-name nunca foi executado ou a última execução foi concluída
  user: "execute o workflow workflow-name"
  commentary: iniciar nova execução — passar --new para workflow-runner
  </example>

  <example>
  Context: existe execução com tarefa status paused (human step pendente)
  user: "<resposta ao human step>"
  commentary: retomar execução pausada — passar --resume para workflow-runner
  </example>

tools: Read, Write, Bash, Agent
skills: [workflow-runner, backlog-worker]
model: opus
color: purple

# mcpServers gerados a partir do campo integrations em ## Definição
# mcpServers:
#   <integration>: ...

# ── amflow — rastreabilidade ───────────────────────────────────────────────────
type: agent
project: ""
author: ""
author_id: ""
created: ""
status: draft
version: 1.0.0
updated: ""
scope: project
auto_load: false
tags: [workflow]
dependencies: [workflow-runner, backlog-worker]

# ── amflow — hub (preenchido automaticamente pelo amflow-publish) ──────────────
hub_id: ""
source: ""
price: 0
---

Ao ser invocado, usar a skill `workflow-runner` passando os argumentos recebidos.
A definição do workflow está na seção ## Definição abaixo.

## Definição

```yaml
schedule: ""                # cron expression — vazio = execução manual
max_loop_iterations: 5      # limite global de iterações por loop
integrations: []            # MCPs necessários (ex: google-drive, gmail, web-search)

nodes:
  - id: node-id
    label: "Label do nó"
    type: agent             # agent | human
    agent: ""               # nome do agent responsável (se type: agent)
    skills: []              # skills ativas neste nó
    integrations: []        # MCPs específicos do nó (complementa o campo acima)
    output_template: |
      ## Seção 1
      ## Seção 2
      ## Campo-condicional: <valor-a|valor-b>

  # Exemplo de nó human:
  # - id: revisao
  #   label: "Revisão pelo usuário"
  #   type: human
  #   description: "Revise o resultado e preencha o template abaixo."
  #   output_template: |
  #     ## Decisão: <aprovado|reprovado>
  #     ## Comentários

edges:
  # Transição incondicional:
  - from: node-id
    to: next-node-id
    condition: null

  # Transição condicional (múltiplas arestas — avaliadas na ordem):
  # - from: node-id
  #   to: branch-a
  #   condition: "output.campo == valor-a"
  #
  # - from: node-id
  #   to: branch-b
  #   condition: "output.campo == valor-b"

  # Loop (back-edge):
  # - from: node-id
  #   to: node-id
  #   condition: "output.qualidade != high"
  #   loop:
  #     max_iterations: 3
  #     on_max: continue    # fail | skip | continue
```

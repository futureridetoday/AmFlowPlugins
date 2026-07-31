---
# ── campos nativos do claude code ──────────────────────────────────────────────
name: agent-name
# TRIGGER DE INVOCAÇÃO: Claude lê este campo para decidir se o agente é relevante para a tarefa.
# Responda DUAS perguntas: o que faz + quando usar. Exemplos concretos aumentam precisão de matching.
description: |
  <o que faz — uma frase objetiva>
  Use when <situação específica que ativa este agente>.

  <example>
  Context: <contexto que ativa este agente>
  user: "<mensagem do usuário>"
  commentary: <por que invocar este agente neste momento>
  </example>

# ferramentas (allowlist). omitir para herdar tudo do pai.
# Read,Grep,Glob       → somente leitura
# + Bash               → + execução shell
# + Edit               → + edição de arquivos existentes
# + Write              → + criação de arquivos
# + Agent              → + capacidade de invocar subagentes (obrigatório para orquestradores)
tools: Read, Grep, Glob, Bash
# disallowedTools:               # opcional — denylist, alternativo a tools

# model: haiku (rápido) | sonnet (padrão) | opus (raciocínio profundo) | inherit
model: inherit

# color: blue(análise/review) | green(geração) | red(segurança) | cyan(docs)
#        yellow(validação)    | pink(refactoring) | purple(orquestração) | orange(infra)
color: blue

# ── recursos opcionais ──────────────────────────────────────────────────────────
# permissionMode:                # default | acceptEdits | auto | dontAsk | bypassPermissions | plan
# maxTurns:                      # máximo de turns antes de parar
# background:                    # true = sempre roda em background
# effort:                        # low | medium | high | xhigh | max
# isolation:                     # worktree = git worktree isolado

# SKILLS — como o agente escolhe quais skills usar (dois modelos):
#
#   MODELO 1 — Trigger por descrição (Anthropic nativo)
#   O Claude lê o campo `description` de todas as skills instaladas no startup e faz
#   matching com a tarefa atual. A skill é carregada automaticamente quando a descrição
#   corresponde. Bom para skills independentes reutilizáveis por múltiplos agentes.
#
#   MODELO 2 — Mapeamento explícito (fluxos sequenciais)
#   O agente declara no Processo qual skill carregar para cada tarefa. O Claude segue
#   a instrução diretamente, sem matching. Bom para fluxos determinísticos com ordem
#   obrigatória. Declare no Processo:
#     Bash: cat .claude/skills/<nome>/SKILL.md  → segue as instruções da skill
#
#   PRÉ-CARREGAMENTO (campo abaixo): injeta skills no startup, antes da primeira tarefa.
#   Use apenas para skills invariavelmente necessárias — aumenta custo de contexto.
# skills:
#   - skill-name

# memory:                        # user | project | local — persiste entre sessões

# mcpServers:                    # servidores MCP escopados a este agente (mapeamento, não lista)
#   server-name:                 # referência a servidor já configurado na sessão
#   my-server:                   # definição inline (conecta no startup, desconecta no fim)
#     type: stdio
#     command: npx
#     args: ["-y", "@org/mcp@latest"]

# hooks:                         # hooks de ciclo de vida (só ativos durante este agente)
#   PreToolUse:
#     - matcher: "Bash"
#       hooks:
#         - type: command
#           command: "./scripts/validate.sh"
#   PostToolUse:
#     - matcher: "Edit|Write"
#       hooks:
#         - type: command
#           command: "./scripts/lint.sh"

# initialPrompt:                 # turn automático quando roda como sessão principal via --agent

# ── amflow — hard memory ───────────────────────────────────────────────────────
# Persiste contexto entre sessões em arquivo de texto lido/escrito pelo agent.
# Requer skill `hard-memory` instalada (incluída no plugin AmFlow base).
# hard_memory:
#   enabled: true
#   scope: project              # project (.claude/hard-memory/) | global (~/.claude/hard-memory/)
#   strategy: rewrite           # rewrite (estado consolidado) | append (histórico completo)
#   compaction_threshold: 80    # linhas — acima disso, compactar antes de escrever

# ── amflow — rastreabilidade ───────────────────────────────────────────────────
type: agent
project: ""
author: ""
author_id: ""              # uuid do usuário autenticado (tool me) — atribuição (L0), preenchido pelo Builder na Fase 0; não é âncora de confiança
created: ""                # YYYY-MM-DD
status: stable             # draft | review | stable | deprecated
version: 1.0.0
updated: ""
scope: project             # global | project
auto_load: false
tags: []
dependencies: []
d1: ""                     # vertical: dev | product | design | data | marketing | sales | support | ops | finance | hr | legal | security | logistics
d2: ""                     # função dentro da vertical (ex: Dev Frontend · Data Analyst · Copywriter)
d4: ""                     # output: report | code | content | file | action | feedback

# ── amflow — hub (preenchido automaticamente pelo amflow-publish) ──────────────
hub_id: ""
source: ""                 # hub/<tipo>/<nome>@<versão> | local
price: 0                   # centavos — usado na publicação; 0 = gratuito (definido pelo Creator, não preenchido automaticamente)
---

# [Nome do Agente]

<!-- Identidade: "You are a [role] specializing in [domain]."
     Uma frase. Define papel e especialização. -->

## Responsabilidades

<!-- O que este agente faz — 2 a 5 itens numerados.
     Cada item deve ser uma ação concreta e verificável. -->

1. <responsabilidade 1>
2. <responsabilidade 2>

## Fora do Escopo

<!-- O que este agente explicitamente não faz.
     Previne expansão de escopo por ambiguidade.
     Mínimo 1 item. -->

- <o que não faz>

## Entradas

<!-- Declare o que o agente precisa receber para funcionar.
     Para cada input: fonte esperada, obrigatoriedade e comportamento se ausente.
     "bloqueia" = agente para e informa. "continua com limitação" = prossegue declarando a restrição no output. -->

| Input | Fonte | Obrigatório | Se ausente |
|---|---|---|---|
| <nome> | <origem> | Sim | bloqueia |
| <nome> | <origem> | Não | continua com limitação declarada |

## Processo

<!-- Passos que o agente segue quando invocado.
     Prescritivo: o agente executa e retorna — não itera, não pergunta.
     Se o agente usa skills sob demanda, inclua o passo de leitura explícita:
       Bash: cat .claude/skills/<nome>/SKILL.md  → segue as instruções da skill -->

Quando invocado:
1. <passo 1>
2. <passo 2>

## Decide Sozinho

<!-- Decisões que o agente toma sem consultar o usuário.
     Liste apenas o que pode ser ambíguo — o óbvio não precisa estar aqui. -->

- <decisão autônoma>

## Escala para o Usuário

<!-- Situações que exigem retorno ao humano antes de prosseguir.
     Inclua: ambiguidades que comprometem a execução, ações irreversíveis, conflitos irresolvíveis.
     Formato: "<situação>: <o que apresentar ao usuário>" -->

- <situação>: <o que apresentar>

## Padrões de Qualidade

<!-- Critérios que o output precisa satisfazer.
     Inclua apenas o que é verificável objetivamente. -->

- Verificar via output de ferramenta — nunca assumir que uma ação teve efeito sem confirmar o resultado
- <critério específico do agente>

## Output

<!-- Formato exato do que o agente retorna — uma única mensagem.
     Defina estrutura, seções e exemplo quando necessário.
     Nunca retornar mais de uma mensagem. Nunca pedir confirmação. -->

```
[template do output]
```

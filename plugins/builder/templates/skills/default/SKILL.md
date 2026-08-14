---
# → Guia de preenchimento por tipo: GUIDE.md

# ── claude code — campos nativos ──────────────────────────────────────────────
name: skill-name           # igual ao nome do diretório · max 64 chars · somente lowercase, números e hífens · sem hífen inicial, final ou consecutivo
description: ""            # imperativo: "Use when..." | o que faz + quando usar (máx 1.024 chars)

# ── claude code — opcionais ────────────────────────────────────────────────────
license: ""                # ex: MIT | Apache-2.0 | Proprietary
compatibility: ""          # dependências de runtime: agente, pacotes de sistema, rede (máx 500 chars)
when_to_use: ""            # contexto adicional de ativação — complementa description

# módulos instalados — uma chave por módulo, escrita pelo /amflow-builder:install-module.
# Não editar à mão: é daqui que a propagação descobre quais skills consomem cada módulo.
# metadata:
#   amflow.module.task-flow: "1.2.0"

# controle de invocação
disable-model-invocation: false   # true = só usuário pode invocar via /skill-name
user-invocable: true              # false = oculta do menu /; só Claude invoca

# ferramentas
allowed-tools: ""          # pré-aprovadas sem prompt: ex "Bash(git *) Read"
disallowed-tools: ""       # removidas do pool enquanto a skill está ativa

# argumentos
argument-hint: ""          # hint no autocomplete: ex "[issue-number]"
arguments: []              # nomes posicionais: ex [issue] → $issue no corpo

# execução
model: ""                  # sobrescreve o modelo (inherit = mantém o ativo)
effort: ""                 # low | medium | high | xhigh | max
context: ""                # fork = executa em subagente isolado
agent: ""                  # tipo de subagente quando context: fork
paths: []                  # glob patterns que restringem ativação por arquivo
shell: ""                  # bash (padrão) | powershell

# hooks de ciclo de vida (só ativos durante esta skill)
# hooks:
#   PreToolUse:
#     - matcher: "Bash"
#       hooks:
#         - type: command
#           command: "./scripts/validate.sh"

# ── amflow — rastreabilidade ───────────────────────────────────────────────────
type: skill
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

# ── referências de criação ────────────────────────────────────────────────────
# [1] Agent Skills open standard (specification)  https://agentskills.io/specification
# [2] Claude Code — Extend Claude with skills     https://code.claude.com/docs/en/skills
---

# [Nome da Skill]

## O que faz

<!-- Responsabilidade única desta skill em uma frase. -->

## Quando usar

<!-- Contextos que ativam esta skill. Específico para evitar falsos positivos.
     Incluir casos onde o usuário não menciona o domínio diretamente. -->

## Não usar quando

<!-- Contextos onde esta skill não se aplica. -->

## Gotchas

<!-- Fatos específicos do ambiente que o agente erraria sem ser informado.
     Não usar para boas práticas genéricas — apenas correções concretas.
     Exemplo:
     - A tabela `users` usa soft delete — queries precisam de `WHERE deleted_at IS NULL`
     - O campo é `user_id` no banco, `uid` na auth e `accountId` no billing
-->

## Argumentos

<!-- Remover esta seção se `arguments` não estiver configurado no frontmatter.
     - $nome      — descrição do argumento
     - $ARGUMENTS — todos os argumentos brutos passados pelo usuário
-->

## Contexto Dinâmico

<!-- Remover esta seção se a skill não usar shell injection.
     Inline:  !`git diff --stat HEAD`
     Bloco:   ```!
              gh pr view --json title,body
              ```
-->

## Scripts

<!-- Remover esta seção se a skill não usar scripts/.
     Usar scripts/ quando a lógica é específica do projeto, precisa de consistência
     entre execuções ou é complexa demais para um único comando.
     Para ferramentas existentes, referenciar diretamente com versão fixada:
       uvx ruff@0.8.0 check .   |   npx eslint@9 --fix .
     Scripts em scripts/ são invocados explicitamente nas ## Instruções.
     - scripts/analyze.py   — inspeção / leitura
     - scripts/validate.py  — validação do plano
     - scripts/execute.py   — execução final

     Boas práticas obrigatórias:
     - Sem prompts interativos: aceitar todos os inputs via flags ou stdin — nunca bloquear em TTY
     - Erros acionáveis: "Campo 'X' não encontrado — disponíveis: A, B, C" em vez de "input inválido"
     - stdout para dados, stderr para logs — Claude lê stdout; misturar logs polui o contexto
     - Idempotente: "criar se não existir" em vez de "criar e falhar em duplicata"
-->

<!-- Módulos instalados. A região abaixo é escrita pelo /amflow-builder:install-module —
     não editar à mão: o conteúdo entre os marcadores é substituído a cada instalação e a
     cada propagação de versão. Fica vazia enquanto a skill não usa módulo nenhum, e nesse
     caso não renderiza nada.

     Cada linha aponta direto para o MODULE.md daquele módulo, pelo caminho completo. Nunca
     substituir as linhas por "veja modules/" — o agente precisa do ponteiro, não do convite
     a navegar. -->
<!-- modules:start -->
<!-- modules:end -->

## Instruções

<!-- Passos que o Claude executa. Liste ações, critérios e formato de output.
     Calibrar o nível de prescrição pela fragilidade da operação:
     - Operações irreversíveis: prescritivo, sequência exata
     - Abordagem geral: dar liberdade, explicar o porquê
     1. ...
     2. ...
-->

## Invariantes

<!-- Condições que nunca podem ser violadas por esta skill.
     Exemplo:
     - Nunca sobrescrever arquivo sem confirmação quando versão existente é mais recente
     - Nunca instalar sem token de sessão válido
-->

## Output

<!-- Formato exato do que a skill entrega.
     Para formatos complexos, incluir um template inline ou referenciar assets/template.md
-->

## Exemplos

<!-- Remover esta seção se os exemplos já estiverem inline em ## Instruções.
     Para casos concretos de input → output que ajudam outros a entender a skill.
     Para exemplos longos, referenciar assets/exemplo.md
-->

## Referências

<!-- Arquivos que a skill deve consultar. Máximo 1 nível de profundidade.
     - `.claude/CLAUDE.md`
     - `references/REFERENCE.md`
-->

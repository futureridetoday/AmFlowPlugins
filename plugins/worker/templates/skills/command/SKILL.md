---
# ── skill de tarefa (task content) invocada pelo usuário ──────────────────────
# O formato commands/ foi incorporado às skills: "Custom commands have been merged into skills" [2].
# Uma skill de tarefa é "step-by-step instructions for a specific action" que o usuário invoca
# com /<plugin>:<nome> — e a doc recomenda disable-model-invocation: true para ela [2].

# ── especificação Agent Skills — sempre presentes ─────────────────────────────
name: skill-name           # igual ao nome do diretório · é o nome do comando: /<plugin>:skill-name · max 64 chars · somente lowercase, números e hífens · sem hífen inicial, final ou consecutivo
description: ""            # o que o comando faz, em uma frase — aparece no menu /; com disable-model-invocation o Claude não a usa para decidir invocar (máx 1.024 chars)
license: ""                # ex: MIT | Apache-2.0 | Proprietary — obrigatório no AmFlow

# ── claude code — o que faz desta skill um comando ────────────────────────────
disable-model-invocation: true   # só o usuário invoca, com /<plugin>:<nome> — o Claude não dispara sozinho [2]

# ── claude code — só quando o campo carrega comportamento ─────────────────────
# Nunca declarar valor default: descomentar é ato deliberado, não preenchimento de formulário.
# Ausentes de propósito: when_to_use e paths só servem à ativação automática, que este tipo
# desliga; user-invocable: false contradiz o tipo.

# argument-hint: ""            # hint no autocomplete: ex "[--price <centavos>]" — só quando o comando aceitar argumentos
# arguments: []                # nomes posicionais: ex [type, name] → $type e $name no corpo — só quando houver argumentos posicionais
# allowed-tools: ""            # pré-aprovadas enquanto o comando roda — ex "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/x.py *)"
# disallowed-tools: ""         # removidas do pool enquanto o comando está ativo — ex "Write Edit" quando só o agent pode escrever
# effort: ""                   # low | medium | high | xhigh | max — só quando o comando exigir nível diferente do da sessão
# model: ""                    # só quando o comando exigir um modelo específico (inherit é o padrão, não declarar)
# shell: powershell            # só quando powershell — bash é o default, não declarar

# context: fork                # NÃO usar quando o comando conversa com o usuário: o subagente "doesn't see your
# agent: ""                    # conversation history" e roda em background por padrão [2]. Só para comando sem
# background: false            # pergunta nem confirmação — nesse caso, agent e background acompanham o fork.

# hooks:                       # só quando o comando registrar hook de ciclo de vida
#   PreToolUse:
#     - matcher: "Bash"
#       hooks:
#         - type: command
#           command: "./scripts/validate.sh"

# ── dado próprio do AmFlow — nunca no topo, sempre em metadata ────────────────
# Prefixo amflow- em kebab-case, valor sempre string — a spec define metadata como mapa
# de string para string, e valor que não seja string é descartado.
# As sete chaves descomentadas são obrigatórias desde a criação — presentes sempre, e
# com valor exceto amflow-dependencies, que pode ficar vazia.
# amflow-hub-id só existe após a 1ª publicação. amflow-source nunca aparece aqui: só na
# cópia instalada, nunca no repositório do Creator.
metadata:
  amflow-version: "1.0.0"
  amflow-status: in_progress
  amflow-author: ""
  amflow-author-id: ""
  amflow-updated: ""         # YYYY-MM-DD
  amflow-tags: ""            # separadas por espaço, kebab-case — nunca lista
  amflow-dependencies: ""    # type/name@version separadas por espaço — vazio quando não há dependência
  # amflow-hub-id: ""        # uuid atribuído pelo Hub — só existe após a 1ª publicação

# ── referências de criação ────────────────────────────────────────────────────
# [1] Agent Skills open standard (specification)  https://agentskills.io/specification
# [2] Claude Code — Extend Claude with skills     https://code.claude.com/docs/en/skills
# [3] Claude Code — Subagents                     https://code.claude.com/docs/en/sub-agents
---

# /plugin-name:skill-name

<!-- Padrão: o comando conversa, o agent executa. Esta skill resolve pré-condições, pergunta ao
     usuário e pede a confirmação; depois invoca um agent uma única vez, que faz o trabalho com
     as próprias ferramentas e devolve um relatório. O agent nunca conversa com o usuário.

     Corpo enxuto: depois de invocada, a skill "stays in context across turns" [2] — toda linha
     é custo recorrente. Dizer o que fazer, não narrar como nem por quê. -->

## O que faz

<!-- Responsabilidade única do comando em uma frase, e qual agent executa o trabalho. -->

## Gotchas

<!-- Fatos específicos do ambiente que o agente erraria sem ser informado.
     Não usar para boas práticas genéricas — apenas correções concretas. -->

## Argumentos

<!-- Remover esta seção se o comando não aceitar argumentos.
     - $nome      — descrição do argumento
     - $ARGUMENTS — todos os argumentos brutos passados pelo usuário
-->

## Contexto Dinâmico

<!-- Remover esta seção se o comando não usar shell injection.
     Inline:  !`git status --short`
-->

## Instruções

### Fase 1 — Pré-condições

<!-- O que precisa ser verdade antes de perguntar qualquer coisa: sessão válida (tool me),
     projeto resolvido, dados listados por tool ou script. Falhou → encerrar com a mensagem,
     sem invocar o agent. -->

### Fase 2 — Confirmação humana (M10)

<!-- Obrigatória antes de qualquer escrita. Exibir o que será feito e usar AskUserQuestion:
     "Confirmar" ou "Cancelar". Cancelar encerra sem invocar o agent. -->

### Fase 3 — Execução

<!-- Invocar o agent uma vez, com o identificador registrado (plugin:pasta:nome), e só depois da
     confirmação:

     Agent(
       subagent_type: "<plugin>:<agent>:<agent>",
       run_in_background: false,
       prompt: "Chave: valor\nChave: valor"
     )

     Numa sessão interativa o subagente roda em background mesmo com run_in_background: false —
     "Claude can't ask for the foreground" [3]. Então esperar: no máximo uma linha dizendo que o
     trabalho está em andamento, sem adivinhar o resultado. O relatório chega como mensagem do
     subagente; tratá-lo como o retorno da chamada. -->

### Fase 4 — Resultado

<!-- Ler a linha RESULTADO: do relatório do agent e mapear cada valor para o que exibir.

     | RESULTADO | O que fazer |
     |---|---|
     | OK        | ... |
     | ERRO      | ... |
-->

## Invariantes

<!-- Condições que nunca podem ser violadas por este comando.
     - Nunca invocar o agent antes da confirmação da Fase 2
     - Nunca escrever arquivo nesta skill — quem escreve é o agent
-->

## Output

<!-- O que o usuário vê ao final — a mensagem de cada RESULTADO da Fase 4. -->

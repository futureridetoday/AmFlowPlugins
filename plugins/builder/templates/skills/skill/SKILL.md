---
# ── especificação Agent Skills — sempre presentes ─────────────────────────────
name: skill-name           # igual ao nome do diretório · max 64 chars · somente lowercase, números e hífens · sem hífen inicial, final ou consecutivo
description: ""            # imperativo: "Use when..." | o que faz + quando usar (máx 1.024 chars)
license: ""                # ex: MIT | Apache-2.0 | Proprietary — obrigatório no AmFlow

# ── especificação Agent Skills — condicionais ──────────────────────────────────
# Nunca declarar sem necessidade real — campo presente e não usado é ruído.
# compatibility: ""          # só quando houver requisito real de ambiente (máx 500 chars) — a maioria das skills não precisa
# allowed-tools: ""          # só quando a skill precisar de ferramenta pré-aprovada — ex "Bash(git *) Read"

# ── claude code — só quando o campo carrega comportamento ─────────────────────
# Nunca declarar valor default: descomentar é ato deliberado, não preenchimento de formulário.

# when_to_use: ""            # só quando o gatilho não couber no description — é anexado a ele na listagem, e os dois somam no teto de 1.536 chars

# disable-model-invocation: true   # só quando true — default é false, não declarar
# user-invocable: false            # só quando false — default é true, não declarar
# paths: []                        # glob patterns que restringem ativação por arquivo — só quando a ativação for restrita

# context: fork                # só quando fork — executa em subagente isolado
# agent: ""                    # tipo de subagente — só quando context: fork
# background: false            # só quando false, e só com context: fork — espera o subagente na mesma vez
# effort: ""                   # low | medium | high | xhigh | max — só quando a skill exigir nível diferente do da sessão
# model: ""                    # só quando a skill exigir um modelo específico (inherit é o padrão, não declarar)
# shell: powershell            # só quando powershell — bash é o default, não declarar

# arguments: []                # nomes posicionais: ex [issue] → $issue no corpo — só quando houver argumentos
# argument-hint: ""            # hint no autocomplete: ex "[issue-number]" — só quando houver arguments
# disallowed-tools: ""         # removidas do pool enquanto a skill está ativa — só quando a skill nunca puder chamar certa ferramenta

# hooks:                       # só quando a skill registrar hook de ciclo de vida
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
  amflow-status: draft
  amflow-author: ""          # git config user.name — preenchido pelo Builder na Fase 0
  amflow-author-id: ""       # uuid do usuário autenticado (tool me) — preenchido pelo Builder na Fase 0
  amflow-updated: ""         # YYYY-MM-DD
  amflow-tags: ""            # separadas por espaço, kebab-case — nunca lista
  amflow-dependencies: ""    # type/name@version separadas por espaço — vazio quando não há dependência
  # amflow-hub-id: ""        # uuid atribuído pelo Hub — só existe após a 1ª publicação, escrito pelo amflow-publish
  # amflow.module.<nome>: "" # registro de módulo instalado — escrito pelo /amflow-builder:install-module, não editar à mão

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

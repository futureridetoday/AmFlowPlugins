---
# ── amflow — rastreabilidade ───────────────────────────────────────────────────
name: command-name
type: command
project: ""
description: ""
tags: []
author: ""
author_id: ""              # uuid do usuário autenticado (tool me) — atribuição (L0), preenchido pelo Builder na Fase 0; não é âncora de confiança
created: ""                # YYYY-MM-DD
status: stable             # draft | review | stable | deprecated
version: 1.0.0
updated: ""
scope: project             # global | project
auto_load: false
dependencies: []
d1: ""                     # vertical: dev | product | design | data | marketing | sales | support | ops | finance | hr | legal | security | logistics
d2: ""                     # função dentro da vertical (ex: Dev Frontend · Data Analyst · Copywriter)
d4: ""                     # output: report | code | content | file | action | feedback

# ── amflow — hub (preenchido automaticamente pelo amflow-publish) ──────────────
hub_id: ""
source: ""                 # hub/<tipo>/<nome>@<versão> | local
price: 0                   # centavos — usado na publicação; 0 = gratuito (definido pelo Creator, não preenchido automaticamente)
---

# [Nome do Command]

## O que faz

<!-- Responsabilidade única deste command em uma frase. -->

## Quando usar

<!-- Contextos que ativam este command. Específico para evitar falsos positivos. -->

## Argumentos

<!-- Remover esta seção se o command não aceita argumentos.
     - $nome      — descrição do argumento
     - $ARGUMENTS — todos os argumentos brutos passados pelo usuário
-->

## Instruções

<!-- Passos que o Claude executa quando o command é invocado.
     Calibrar o nível de prescrição pela fragilidade da operação:
     - Operações irreversíveis: prescritivo, sequência exata
     - Abordagem geral: dar liberdade, explicar o porquê
     1. ...
     2. ...
-->

## Output

<!-- Formato exato do que o command entrega ao usuário. -->

## Referências

<!-- Arquivos que o command deve consultar. Máximo 1 nível de profundidade.
     - `.claude/CLAUDE.md`
     - `references/REFERENCE.md`
-->

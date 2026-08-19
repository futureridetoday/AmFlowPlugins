---
# about
name: backlog
type: doc
project: AmFlowPlugins
description: Registro de problemas, ideias e features antes de virarem plano — o passo anterior ao plano no _inbox. Item daqui não tem número, não entra em _planos.md e não segue o formato de plano
tags: [backlog, plan, inbox, triagem, dev-units]

# history
author: Bortoli
created: 2026-08-18
status: draft
version: 1.0.0
updated: ""

# system
scope: project
auto_load: false
dependencies: []
---

# Backlog

Onde problema, ideia e feature ficam registrados **antes** de virarem plano.

O modelo dev-units começa no plano, e plano já é um compromisso: nome, alvo declarado, independência
argumentada, escopo em unidades. Muita coisa que vale registrar ainda não merece esse custo — ou
porque não está madura, ou porque ninguém decidiu se vai ser feita. Sem um lugar antes do plano, essas
coisas vivem em conversa e se perdem.

## O que isto não é

- **Não é plano.** Item daqui não tem `plan_id`, não recebe número, não entra em
  [`_planos.md`](plan/_planos.md) e não segue o formato de plano.
- **Não é projeção de script.** O arquivo é escrito à mão, inteiro. Em particular, **não usar os
  marcadores `<!-- backlog:start -->` / `<!-- backlog:end -->`** aqui: eles pertencem ao
  [`backlog.py`](../.claude/skills/dev-units/scripts/backlog.py), que projeta o backlog de *unidades*
  dentro do arquivo de um plano. Nome igual, mecanismo oposto — e o script sobrescreve o miolo sem
  perguntar.
- **Não é lista de tarefas.** Tarefa de execução vive na unidade, com contrato e critério de aceite.

## Como um item sai daqui

Vira plano no [`plan/_inbox/`](plan/_inbox/), com nome próprio — a linha se move de **Problemas
abertos** para **Solução planejada**, com o id do plano. Quando o plano é implementado e o item
verificado, a linha se move para **Problemas resolvidos**, com a data de conclusão. Ou é descartado, e
sai da tabela com o porquê registrado na mensagem do commit — descarte sem motivo escrito volta como a
mesma ideia daqui a três meses.

Nada em **Problemas abertos** ou **Solução planejada** está aprovado por estar aqui. Estar no backlog
é estar registrado, não estar decidido.

## Itens

Três tabelas, uma por estado. Um item existe em exatamente uma delas por vez — a seção acima descreve
como ele se move entre as três.

Campos de vocabulário fechado:

- **Prioridade** — `urgente` (reservado a problema em produção) · `importante` · `normal` · `baixa`
- **Autor** — `Claude` ou o nome de quem identificou o item
- **Core** — `builder` · `worker` · `marketplace` · outros, conforme o item exigir

**Item pode nascer fora deste repositório.** O que decide a entrada é onde está a **correção**, não
onde o sintoma apareceu. Um defeito observado numa skill do repositório de recursos entra aqui quando
o que precisa mudar é o Builder ou o Worker; a coluna *Onde vive* registra os dois lados.

### Problemas abertos

| # | Item | Tipo | Prioridade | Autor | Core | Data de inclusão | Onde vive |
|---|---|---|---|---|---|---|---|
| B-01 | **O layout que o `install-module` escreve não é o layout que o módulo descobre.** Encontrado em 2026-08-18, na revisão de prontidão da skill `primal-branding` (repositório de recursos, `skills/primal-branding/`). O [`install-module`](../plugins/builder/skills/install-module/SKILL.md) fixa dois destinos — cópia instalada em `<skill>/modules/<nome>/`, configuração em `<skill>/config/<nome>.json`. O `data_insights.py`, quando não recebe `--manifest`, procura o manifesto em `<script>/../config/` e `<script>/config/`, e a própria docstring entrega a herança: *"`config/` na raiz da skill (um nível acima de `scripts/`)"*. A heurística foi escrita para um módulo em `<skill>/scripts/`; instalado onde o Builder manda, ela resolve `modules/config/data-insights.json` e `modules/data-insights/config/data-insights.json` — **nenhum dos dois existe**. **Medido:** `python3.10 modules/data-insights/data_insights.py list --dir <tmp>` falha com `config/data-insights.json não encontrado`; com `--manifest config/data-insights.json` o comando roda e a view é gerada corretamente. **É defeito latente, não ativo.** Não dispara hoje porque nenhuma das duas skills consumidoras (`primal-branding`, `golden-circle`) chega a invocar o módulo pelo corpo do `SKILL.md` — a chamada nunca acontece, então a descoberta nunca falha. Dispara na primeira skill que ligar o módulo ao procedimento, que é exatamente o próximo passo natural de ambas. **Quem paga o silêncio:** o `MODULE.md` trata `--manifest` como flag de conveniência (*"aceitas antes ou depois do subcomando"*), e afirma que `${CLAUDE_SKILL_DIR}` é *"resolvida no `SKILL.md`"* — não é, em nenhuma das duas skills. Quem seguir a documentação como está escrita não passa a flag e não tem como saber que precisa. **O que decidir:** de que lado a contradição se resolve — o `install-module` passa a escrever a invocação com `--manifest` no bloco de módulos instalados da skill; ou a heurística do módulo aprende o layout `modules/<nome>/` que o Builder de fato usa; ou a configuração muda de lugar. O primeiro caminho corrige por instalação e deixa o módulo errado; o segundo corrige o módulo e não alcança as cópias já materializadas, que só se atualizam por propagação | problema | importante | Claude | builder | 2026-08-18 | `/amflow-builder:install-module` (Builder) · módulo `data-insights` e skills consumidoras (repositório de recursos) |

### Solução planejada

| # | Item | Tipo | Prioridade | Autor | Core | Data de inclusão | Onde vive | Plano |
|---|---|---|---|---|---|---|---|---|

_Nenhum item ainda._

### Problemas resolvidos

| # | Item | Tipo | Prioridade | Autor | Core | Data de inclusão | Onde vive | Plano | Data de conclusão |
|---|---|---|---|---|---|---|---|---|---|

_Nenhum item ainda._

---
# about
name: build
type: command
project: AmFlow
description: Cria um novo recurso (skill, agent ou module) — para skill, por survey guiado, importando um recurso existente, ou a partir do template puro; agent e module partem do template com o nome
tags: [build, resource, scaffold, creator, template, module]

# history
author: Bortoli
created: 2026-06-14
status: stable
version: 1.0.0
updated: "2026-09-10"

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-builder:build

Cria um novo recurso AmFlow. Tipos suportados: `skill`, `agent`, `module` — redução temporária, até cada tipo ter seu fluxo dedicado (`hook`, `command`, `plugin` e `workflow` saem por ora). Para `skill`, o Creator escolhe o método de criação — survey guiado, importar um recurso existente, ou partir do template puro. `agent` e `module` partem do template com o nome.

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → guarde o `user_id` retornado para carimbar `author_id` no recurso gerado (Fase 3). Com sessão já ativa, o `me` responde direto e o comando segue sem novo login.
- Sem sessão / erro → o conector `amflow-builder` não está autorizado nesta sessão. **Encerre aqui** — não crie nenhum arquivo. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

## Fase 1 — Projeto e tipo

1. Identificar o projeto de destino:
   - Executar `pwd` → exibir caminho atual como sugestão. Aceitar "Informar outro caminho" (texto livre).
   - Validar que o caminho contém `.claude/CLAUDE.md` → encerrar com erro se ausente: **"Projeto não encontrado em: <caminho> — verifique se o diretório contém .claude/CLAUDE.md"**
   - Ler o nome do projeto no `.claude/CLAUDE.md` como `project_name` (Fase 3, **De onde sai o `project`**).

2. Perguntar o tipo de recurso:

   | Tipo | Descrição |
   |---|---|
   | `skill` | instrução com frontmatter — ativada sob demanda |
   | `agent` | subagente com ferramentas e instruções próprias |
   | `module` | capacidade reusável que skills instalam — o usuário nunca a invoca |

   **Redução temporária.** `hook`, `command`, `plugin` e `workflow` saem da lista até cada tipo ganhar seu fluxo dedicado. Restaurar um deles é re-adicionar sua linha aqui e seu roteamento na Fase 1.5.

   Fronteira entre `skill` e `module`: **skill é o que o usuário invoca; módulo é o que a skill usa e o usuário nunca vê.** Na dúvida, pergunte quem dispara — se a resposta for "a skill", é módulo.

## Fase 1.5 — Método de criação

### `skill` — escolha de método

Quando o tipo é `skill`, depois do tipo, perguntar o método:

| Método | O que faz |
|---|---|
| Passo a passo | O Claude conduz a criação completa do recurso. |
| Importar | Com ajuda do Claude, um recurso existente é adaptado aos padrões do AmFlow. |
| Usar template | Cria o recurso a partir do modelo padrão do AmFlow. |

Roteamento:

| Método | Rota |
|---|---|
| Passo a passo | Fase 2 (Survey por tipo) → Fase 3 → 3.5 → 4 |
| Importar | Fase 2 (Importar) → Fase 3 → 3.5 → 4 — sem survey |
| Usar template | Fase 2 (Usar template) → Fase 3 → 3.5 → 4 — sem survey |

Só "Passo a passo" entra no survey. Os outros dois pulam a Fase 2 (Survey por tipo).

### `agent`, `module` — caminho mínimo

Sem pergunta de método. Enquanto cada tipo não tem seu fluxo dedicado, seguem direto por nome + template:

1. **Nome** — perguntar, exibindo o método de nomeação do tipo:
   - os dois validam pela **Regra de nome do recurso** (abaixo);
   - `module` soma a varredura de namespace da **Regra de nome do recurso** — colisão rejeita.
2. **Fase 3 direto** — copiar o template do tipo (tabela da Fase 3), substituir os placeholders pelo nome, carimbar só o frontmatter que não depende de survey: `name`, `created`, `project`, `source`, `author`, `author_id`, `status: draft`, e `type` no `agent`. Os campos de survey ficam com o placeholder do template — `description`, `tags`, e `d1`/`d2`/`d4` no `agent`. `module`: o `module.json` recebe `name` + `version: 1.0.0`; `description` fica com o placeholder.
3. **Fase 3.5 pulada** (não é `skill`). **Fase 4**: o esqueleto é entregue — o Creator preenche o conteúdo, incluindo `description` e `tags`, antes de publicar.

O caminho mínimo **não coleta** `description`/`tags` — difere do "Usar template" de `skill`, que coleta por causa do gate da Fase 3.5. Fora de `skill` não há gate no `build`; o `/amflow-builder:publish` cobra os campos depois.

Cada tipo terá seu fluxo próprio depois; por ora `skill` usa o roteamento acima e `agent` e `module`, o caminho mínimo.

### Regra de nome do recurso

Vale para os três métodos de `skill` e para o caminho mínimo, sempre que o Creator digita o nome: **apenas minúsculas e hífens, sem hífen inicial/final, sem hífens consecutivos, ≤ 64 chars.** Para `module`, além disso: varrer `<projeto>/skills/`, `<projeto>/modules/`, `.claude/skills/` e `.claude/modules/` — recurso em desenvolvimento e já promovido; o espaço de nomes é compartilhado, um nome é skill **ou** módulo, nunca ambos; colisão em qualquer um → rejeitar e pedir outro.

As 3 sugestões automáticas de nome só valem no "Passo a passo" de `skill`, onde há `d1`, `d2` e `intencao` para derivá-las. Em "Importar", "Usar template" e no caminho mínimo o nome é entrada de texto livre, validada pela regra acima.

## Fase 2 — Survey por tipo

> **Escopo atual.** Só `skill` via "Passo a passo" chega aqui. As subseções `Agent`, `Hook`, `Plugin`, `Module` e `Workflow` estão sem rota enquanto a redução da Fase 1 vale — `agent` e `module` seguem pelo caminho mínimo da Fase 1.5; `hook`, `command`, `plugin` e `workflow` não são oferecidos. Ficam no arquivo de propósito: restaurar um tipo é re-adicionar sua linha na tabela da Fase 1 e seu roteamento na Fase 1.5.

Faça uma pergunta por vez. Adapte cada pergunta com base nas respostas anteriores. Os steps seguem a ordem definida para cada tipo.

### Skill

**d1 — Vertical:** dev / product / design / data / marketing / sales / support / ops / finance / hr / legal / security / logistics

**d2 — Função** (lista numerada por vertical, "0. Voltar" retorna a d1):

| Vertical | Opções |
|---|---|
| dev | Dev Frontend, Dev Backend, Full Stack, Mobile, Tech Lead / Arquiteto, DevOps / SRE, QA / Tester |
| product | Product Manager, Product Owner, Product Analyst |
| design | UX Designer, UI Designer, UX Researcher, Product Designer, Motion Designer |
| data | Data Analyst, Data Scientist, Data Engineer, BI Analyst, ML Engineer |
| marketing | Copywriter, SEO, Growth / Performance, Social Media, Content Strategist, Brand Manager |
| sales | SDR / BDR, Account Executive, Pre-sales, Account Manager |
| support | Support Agent, Technical Support, Community Manager, Customer Success |
| ops | Operations Manager, Project Manager, Scrum Master, Business Analyst, Procurement Analyst |
| finance | Controller, Financial Analyst, Accountant |
| hr | HRBP, Recruiter / TA, People Ops, L&D |
| legal | Advogado, Compliance Officer, DPO |
| security | Security Analyst, Pentester, CISO, GRC Analyst, Security Engineer |
| logistics | Logistics Analyst, Supply Chain Manager, Warehouse Manager, Logistics Coordinator |

**d3 — Descoberta conversacional:** conduzir adaptando as perguntas às respostas. Encerrar quando houver ao menos dois exemplos concretos.
- "Qual tarefa concreta essa skill executa?"
- "O que um usuário digitaria para acioná-la?"
- "O que ela não deve fazer?"
- "Dê um exemplo de input e o resultado esperado."

**d4 — Tipo de output:** inferir com base nos exemplos de d3 (report / code / content / file / action / feedback). Exibir como sugestão única. "Escolher outro tipo" abre lista completa de 6 opções.

**intencao:** gerar 3 sugestões de descrição com base em d1+d2+d3+d4. Preamble: *"Este campo é lido por outro Claude para decidir quando invocar o recurso — escreva como se estivesse briefando um colega sem contexto."* Oferecer "Outro (descrever)" com assistência: *"Se preferir, descreva em suas palavras e eu escrevo a frase."*

**intencao_revisao:** exibir descrição atual e perguntar "Confirmar" ou "Refinar". Refinar → 3 novas variações → loop até confirmar.

**nome:** 3 sugestões em kebab-case baseadas em d1+d2+intencao:
1. `d1-d2_slug` (ex: `dev-frontend`)
2. `d2_slug-keyword` baseado em exemplos+intencao (ex: `frontend-tokens`)
3. `d1-d2_slug-keyword` (ex: `design-ui-tokens`)

Aceitar "Outro (digitar)". Validar pela **Regra de nome do recurso** (Fase 1.5).

**tags:** 3 conjuntos via checkbox com seleção múltipla. Fontes: d1+d2+d4+recursos instalados (por frequência). Aceitar "Outro (digitar)".

### Agent

Idêntico a Skill. Diferenças:
- d3: perguntas mencionam "agent" (ex: "Qual tarefa concreta esse agent executa?")
- intencao: formato obrigatório `"<o que faz>. Use when <situação específica>."` — necessário para matching do Claude Code.
- intencao_revisao: "Confirmar" → `hard_memory` (não `nome`).
- **hard_memory** (step extra após confirmar intencao):
  - "Não usar" — agent sem memória persistente
  - "Escopo project" — `.claude/hard-memory/<nome>.md`
  - "Escopo global" — `~/.claude/hard-memory/<nome>.md`

  Se escopo selecionado: adicionar campo `hard_memory:` ao frontmatter, injetar passos de leitura no início e escrita no fim do `## Processo`, adicionar `hard-memory` a `dependencies:`, criar arquivo de memória vazio no path configurado.

### Hook

1. **hook_event:** PreToolUse / PostToolUse / Stop / SubagentStop / SessionStart
2. **d3 — Descoberta:** "Qual evento dispara este hook e por quê?", "O que o hook intercepta ou observa?", "O que ele faz — bloqueia, modifica, loga ou notifica?", "Dê um exemplo: evento ocorre → hook faz X."
3. **intencao**, **intencao_revisao**, **nome**, **tags** — mesmo fluxo. `d4` é sempre `action` (preenchido automaticamente — sem perguntar ao Creator).

### Plugin

Steps: d1 → d2 → intencao → intencao_revisao → [intencao_refinada] → nome → tags. Sem d3 e d4.
- d1 e d2: idênticos a Skill.
- intencao: preamble *"Descreva o problema que este plugin resolve — quais recursos ele agrupa e qual valor entrega como conjunto."*

### Module

Steps: d3 → intencao → intencao_revisao → nome → tags. Sem d1, d2 e d4 — módulo não é recurso de vertical nem produz output próprio; quem entrega ao usuário é a skill que o hospeda.

1. **d3 — Descoberta da capacidade:** "Que capacidade este módulo entrega à skill que o adotar?", "Que parte é código determinístico e que parte exige julgamento do agente?", "Ele precisa de configuração diferente por skill?", "Ele persiste algum estado?". Encerrar quando a fronteira código/julgamento estiver clara.
2. **intencao:** preamble *"Descreva a capacidade como quem vai lê-la é o agente de outra skill, que não conhece este módulo."*
3. **intencao_revisao**, **tags** — mesmo fluxo de Skill.
4. **nome:** validar pela **Regra de nome do recurso** (Fase 1.5) — inclui a varredura de namespace que `module` exige.

### Workflow

1. **nome:** texto livre, validado pela **Regra de nome do recurso** (Fase 1.5). Gera dois arquivos: `<nome>-workflow.md` e `<nome>-workflow.mmd` (destino na tabela da Fase 3).
2. **visao_geral:** conversa adaptativa para extrair `descricao`, `nodes` (id, label, type, agent/skills, output_template) e `integracoes`. Perguntas guia: "O que este workflow faz?", "Quais são as etapas e quem executa cada uma?", "Existem etapas condicionais?", "O workflow precisa acessar serviços externos?"
3. **schedule:** Manual / Diário (`0 8 * * *`) / Dias úteis (`0 9 * * 1-5`) / Semanal (`0 8 * * 1`) / Outro (cron expression livre — validar formato).
4. **tags:** 3 conjuntos gerados com base em nome+descricao+integracoes.

## Fase 2 (Importar) — adaptar um recurso existente

Sem survey. Uma pergunta por vez.

1. **Nome** — pedir o nome do novo recurso, exibindo a **Regra de nome do recurso** (Fase 1.5). Validar. Guardar para os passos seguintes.
2. **Fonte** — pedir o caminho da pasta do recurso existente. Ler o conteúdo com as ferramentas de arquivo: estrutura, arquivos, e o frontmatter ou manifesto se houver.
3. **Sanity check de tipo** — se a pasta aparenta ser de outro tipo (ex.: tem `agent.md` e o tipo escolhido é `skill`), avisar e pedir confirmação antes de seguir.
4. **Template do tipo** — ler o template da tabela da Fase 3, o mesmo que "Passo a passo" usa.
5. **Plano de adaptação** — redigir um plano curto: quais arquivos do template serão criados, como o conteúdo do recurso importado mapeia em cada um, o que é mantido, descartado ou reescrito para conformar à norma AmFlow sob o novo nome. Propor a partir do recurso importado: `description`, `tags` e — nos tipos que os carregam no frontmatter (`agent`, `command`, `plugin`) — `d1` / `d2` / `d4`. O frontmatter é carimbado pelas regras da Fase 3; o da origem nunca é copiado literal.
6. **Revisão** — exibir o plano. Creator responde: **confirmar**, **editar** (volta ao passo 5) ou **cancelar** (encerra sem criar nada).
7. **Criação** — confirmado, executar a Fase 3 usando o plano como fonte de conteúdo no lugar das respostas do survey.

## Fase 2 (Usar template) — esqueleto puro

Sem survey. Perguntas mínimas: nome, `description`, `tags` — e, em um tipo, um parâmetro estrutural que a Fase 3 exige.

1. **Nome** — pedir o nome, exibindo a **Regra de nome do recurso** (Fase 1.5). Validar. Guardar.
2. **`description` + `tags`** — pedir os dois campos. Sem `d1`, `d2`, `d3`, `d4`, `intencao_revisao`. São o mínimo para o recurso não nascer inválido: em skill, a Fase 3.5 reprova `description` ou `amflow-tags` vazios; nos demais tipos não há gate no `build`, mas o `/amflow-builder:publish` cobra os mesmos campos depois. Coletar sempre mantém o fluxo único. `module` recebe só `description` — não tem `tags` no `module.json`.
3. **Parâmetro estrutural, só quando o tipo exige:**
   - `hook` → perguntar o `hook_event` (PreToolUse / PostToolUse / Stop / SubagentStop / SessionStart). É o que a Fase 3 usa para escolher o script; sem ele o hook nasce inerte.
   - `workflow` → nada a perguntar; `## Definição` e o `.mmd` nascem vazios (só o esqueleto do template), para o Creator preencher depois.

Depois: Fase 3 com os demais valores de survey vazios — copiar o template, substituir os placeholders pelo `nome`, carimbar o frontmatter que não depende de survey, e gravar `description` e `tags` do passo 2 no lugar que o tipo usa (frontmatter, ou `module.json` no módulo). `d1` / `d2` / `d4` ficam com o valor vazio do template — o Creator preenche depois, como o resto do conteúdo.

## Fase 3 — Criar recurso

| Tipo | Destino | Template |
|---|---|---|
| `skill` | `<projeto>/skills/<nome>/` | `${CLAUDE_PLUGIN_ROOT}/templates/skills/skill/` (copiar diretório inteiro, exceto `GUIDE.md`) |
| `agent` | `<projeto>/agents/<nome>/` | `${CLAUDE_PLUGIN_ROOT}/templates/agents/agent.md` → `<nome>.md`, mais `agent-description.md` do mesmo diretório |
| `hook` | `<projeto>/hooks/<nome>/` | `hook.json` gerado + `${CLAUDE_PLUGIN_ROOT}/templates/hooks/events/<script>.sh` → `hook.sh` (chmod 755) |
| `command` | `<projeto>/commands/<nome>.md` | `${CLAUDE_PLUGIN_ROOT}/templates/commands/command.md` |
| `plugin` | `<projeto>/plugins/<nome>.json` | `${CLAUDE_PLUGIN_ROOT}/templates/plugins/plugin.json` |
| `workflow` | `<projeto>/workflows/<nome>-workflow.md` + `<projeto>/workflows/<nome>-workflow.mmd` | `${CLAUDE_PLUGIN_ROOT}/templates/workflows/workflow-agent.md` |
| `module` | `<projeto>/modules/<nome>/` | `${CLAUDE_PLUGIN_ROOT}/templates/modules/default/` (copiar diretório inteiro) |

`<projeto>` é a pasta que contém `.claude/` — a mesma âncora validada na Fase 1. O recurso nasce **fora** de `.claude/`, em pasta irmã: `build` produz recurso **em desenvolvimento**, e `.claude/` fica reservado ao recurso pronto para uso, que é o que o Claude Code carrega. Criar a pasta do tipo se não existir. A promoção para dentro de `.claude/` é da Fase 4.

Mapeamento hook_event → script: PreToolUse → `pre-tool-use.sh` | PostToolUse → `post-tool-use.sh` | Stop → `stop.sh` | SubagentStop → `subagent-stop.sh` | SessionStart → `session-start.sh`.

**Ler o `GUIDE.md`, nunca apontar para ele.** Ao criar uma `skill`, ler
`${CLAUDE_PLUGIN_ROOT}/templates/skills/skill/GUIDE.md` antes de preencher o `SKILL.md` — arquétipos,
peso de cada seção e padrões de instrução. Ele é legível do lado do plugin; do lado do projeto não
existe, porque a cópia o exclui de propósito.

**Documento de descrição.** Skill, agent e módulo nascem com um `[tipo]-description.md` na raiz da
própria pasta. Em skill e módulo ele vem na cópia de diretório; em agent é copiado à parte. É obrigatório
para publicar no Hub. O bloco de comentários do template é orientação de preenchimento e existe para
ser lido e removido — deixá-lo não reprova no gate, que ignora comentário HTML, mas o documento fica
mais difícil de ler para a próxima pessoa.

Template não encontrado → gerar arquivo com frontmatter completo e seções padrão do tipo.
Recurso já existe → encerrar: **"Recurso já existe: <caminho> — edite-o diretamente ou use /amflow-builder:publish para publicá-lo."**

**Frontmatter:**

| Campo | Valor |
|---|---|
| `name` | `nome` |
| `type` | tipo escolhido |
| `description` | `intencao` |
| `tags` | selecionados |
| `status` | `draft` |
| `d1` / `d2` | coletados (ausentes em hook, workflow e module) |
| `d4` | coletado ou `action` para hook (ausente em plugin, workflow e module) |
| `created` | `date +%Y-%m-%d` |
| `project` | "Nome do projeto" da tabela Identidade do `.claude/CLAUDE.md` (ver abaixo) |
| `source` | `local` |
| `author` | `git config user.name` (local → global); vazio nos dois → perguntar o nome ao Creator. Nunca omitir nem gravar vazio |
| `author_id` | `<user_id>` obtido na Fase 0 — sempre preenchido (a Fase 0 garante sessão autenticada) |

**De onde sai o `project`.** Da linha "Nome do projeto" da tabela `## Identidade` do
`.claude/CLAUDE.md`. É campo declarado, no corpo do arquivo — não frontmatter, que ali não é lido por
nada, e não o título, que é prosa e muda quando alguém edita o `#`.

Duas saídas, nesta ordem, para o `CLAUDE.md` que não tem a linha — projeto configurado à mão, ou
gerado antes desta versão: o título, descartando o sufixo `— Instruções do Projeto` quando houver
(`# Decode and Code — Instruções do Projeto` dá `Decode and Code`); e, se nem isso, o nome da pasta.

Substituir placeholders no template (`skill-name`, `agent-name`, `command-name`, `hook-name`, `plugin-name`, `module-name`) pelo `nome`.

**Module:** a tabela de frontmatter acima **não se aplica** — módulo não tem frontmatter. Sua identidade vive no `module.json`, com três campos: `name` (igual ao do diretório), `version` (inicial `1.0.0`) e `description` (a `intencao` coletada, em uma frase terminada em ponto — a instalação a copia literalmente para a região `modules` da skill, então ela precisa ler bem fora de contexto). O `MODULE.md` é prosa, sem bloco YAML. Remover `config.example.json` do módulo gerado quando o survey indicou que ele não é configurável.

**Workflow:** preencher `## Definição` com nodes e edges extraídos de `visao_geral`. Gerar `<nome>-workflow.mmd` como `flowchart TD` — nós `type: human` com prefixo `👤`, back-edges com sufixo `↻` na label da aresta.

## Fase 3.5 — Verificar a skill gerada

**Só para `skill`.** O verificador aplica a norma de frontmatter de skill e nada mais — rodá-lo sobre
os demais tipos devolve `[R-03] SKILL.md não encontrado`, que é ruído, não achado. Nos demais,
pular esta fase sem mencioná-la.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check.py" <caminho-do-projeto>/skills/<nome>
```

`OK <nome>` e código 0 → Fase 4. `FALHA <nome>` com linhas `[R-XX]` e código 1 → corrigir o campo
apontado e rodar de novo, antes da Fase 4.

Reprovar aqui é defeito do Builder: nesta fase o `SKILL.md` só tem o que o template trouxe e o que a
Fase 3 carimbou. Nunca relatar a skill como verificada sem ter lido `OK` na saída.

**Quando o verificador não roda** — `python3` fora do PATH, ou
`${CLAUDE_PLUGIN_ROOT}/scripts/check.py` ausente numa instalação anterior à vendorização: dizer ao
Creator, em uma linha, que a verificação não rodou e por quê, e seguir para a Fase 4. A skill foi
criada e é entregue; o que faltou foi a conferência.

Ausência não é aprovação. Sem o verificador, a primeira conferência de frontmatter passa a ser a de
`/amflow-builder:publish` — mais tarde, e depois de o Creator já ter tocado o arquivo.

## Fase 4 — Exibir resultado

Listar arquivos criados e orientar próximos passos. Ajustar pelo método:
- **Passo a passo** e **Usar template** entregam esqueleto — o próximo passo é editar o recurso e
  preencher o conteúdo específico.
- **Importar** entrega o recurso já com o conteúdo adaptado do original — o próximo passo é revisar e
  refinar, não escrever do zero.

Sempre:
- Editar o recurso e preencher o conteúdo específico
- Preencher `evals/eval_queries.json` — em skill. Os prompts que devem ativá-la e os *near-miss* que
  não devem. Exigido na publicação
- Quando o recurso estiver pronto, movê-lo de `<projeto>/<tipo>/` para dentro de `.claude/`: `skill` →
  `.claude/skills/<nome>/`, `agent` → `.claude/agents/<nome>/`, `module` → `.claude/modules/<nome>/`. É
  de lá que o Claude Code carrega skill e agent, e de lá que o `/amflow-builder:publish` lê o recurso
- `/amflow-builder:publish` quando o recurso estiver pronto, a partir de `.claude/`

## Restrições

- Um recurso por execução.
- Nome fora da **Regra de nome do recurso** (Fase 1.5) → rejeitar e informar a regra violada.
- `git config user.name` vazio no local e no global → perguntar o nome do autor ao Creator e carimbar
  a resposta. Nunca omitir o campo nem gravá-lo vazio: `amflow-author` é obrigatória **com valor** na
  fonte (R-07), e o agent `reviewer` cobra o mesmo. A tool `me` não serve de saída — devolve só o
  `user_id`, sem perfil.
- Nunca sobrescrever recurso existente.
- Verificador ausente ou não executável não é aprovação — relatar que não rodou.

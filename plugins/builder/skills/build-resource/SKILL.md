---
name: build-resource
description: Cria um novo recurso (skill, agent, command, hook, plugin, workflow ou module) via survey guiado e template — invocada por /amflow-builder:build ou pelo Claude ao detectar intenção de criação
license: Proprietary
metadata:
  amflow-version: "1.0.0"
  amflow-status: review
  amflow-author: Bortoli
  amflow-author-id: 985920db-502d-4cb3-9ca1-c145719a9307
  amflow-updated: "2026-08-27"
  amflow-tags: build resource scaffold creator template module
  amflow-dependencies: ""
---

# Build Resource

Cria um novo recurso AmFlow via survey guiado e template. Invocada quando o Creator quer criar uma skill, agent, command, hook, plugin, workflow ou module.

## Quando usar

- Creator quer criar um novo recurso no projeto
- Invocada por `/amflow-builder:build`
- Claude detecta intenção de criar recurso AmFlow no projeto atual

## Não usar quando

- O recurso já existe — orientar a editar diretamente ou usar `/amflow-builder:publish`

## Processo

### Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → guarde o `user_id` retornado para carimbar `author_id` no recurso gerado (Fase 3). Com sessão já ativa, o `me` responde direto e o processo segue sem novo login.
- Sem sessão / erro → o conector `amflow-builder` não está autorizado nesta sessão. **Encerre aqui** — não crie nenhum arquivo. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reinvocar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

### Fase 1 — Projeto e tipo

1. Verificar se `.claude/CLAUDE.md` existe no projeto atual:
   - Não existe → encerrar: `Projeto não encontrado em: <caminho> — verifique se o diretório contém .claude/CLAUDE.md`
   - Existe → ler e extrair o nome do projeto como `project_name` (Fase 3, **De onde sai o `project`**).

2. Perguntar o tipo de recurso:

   | Tipo | Descrição |
   |---|---|
   | `skill` | instrução ativada sob demanda |
   | `agent` | subagente com ferramentas e instruções próprias |
   | `hook` | script executado em resposta a eventos do Claude Code |
   | `command` | fluxo de execução invocado por /comando |
   | `plugin` | pacote de skills, agents, hooks e commands |
   | `workflow` | processo automatizado com múltiplos agents |
   | `module` | capacidade reusável que skills instalam — o usuário nunca a invoca |

   Fronteira entre `skill` e `module`: **skill é o que o usuário invoca; módulo é o que a skill usa e o usuário nunca vê.** Na dúvida, pergunte quem dispara — se a resposta for "a skill", é módulo.

### Fase 2 — Survey por tipo

Faça uma pergunta por vez. Adapte cada pergunta com base nas respostas anteriores.

**Skill / Command:**
1. `d1` — Vertical: dev, product, design, data, marketing, sales, support, ops, finance, hr, legal, security, logistics
2. `d2` — Função dentro de `d1` (lista numerada por vertical — ex: dev → Dev Frontend, Dev Backend, Full Stack, Mobile, Tech Lead / Arquiteto, DevOps / SRE, QA / Tester). "0. Voltar" retorna a `d1`.
3. `d3` — Descoberta conversacional: "Qual tarefa concreta essa skill executa?", "O que um usuário digitaria para acioná-la?", "O que ela não deve fazer?", "Dê um exemplo de input e resultado esperado". Encerrar quando houver ao menos dois exemplos claros.
4. `d4` — Inferir o tipo de output com base nos exemplos (report / code / content / file / action / feedback). Exibir como sugestão única; "Escolher outro tipo" abre lista completa.
5. `intencao` — Gerar 3 sugestões de descrição com base em d1+d2+d3+d4. Preamble: "Este campo é lido por outro Claude para decidir quando invocar o recurso — escreva como se estivesse briefando um colega sem contexto." Oferecer "Outro (descrever)" com assistência de redação.
6. `intencao_revisao` — Exibir descrição atual e perguntar: "Confirmar" → `nome` | "Refinar" → 3 novas variações → loop até confirmar.
7. `nome` — Gerar 3 sugestões em kebab-case baseadas em d1+d2+intencao. Aceitar "Outro (digitar)". Validar: apenas minúsculas e hífens, sem hífen inicial/final, sem hífens consecutivos, ≤ 64 chars.
8. `tags` — Gerar 3 conjuntos em checkbox com seleção múltipla. Aceitar "Outro (digitar)".

**Agent:** idêntico a Skill/Command. Diferenças:
- `intencao`: formato obrigatório `"<o que faz>. Use when <situação específica>."` — necessário para matching do Claude Code.
- `intencao_revisao`: rota "Confirmar" → `hard_memory` (não `nome`).
- `hard_memory` (step extra): "Não usar" / "Escopo project (`.claude/hard-memory/<nome>.md`)" / "Escopo global (`~/.claude/hard-memory/<nome>.md`)". Se escopo escolhido: adicionar campo `hard_memory:` ao frontmatter, injetar passos de leitura/escrita no `## Processo` e adicionar `hard-memory` a `dependencies:`.

**Hook:**
1. `hook_event` — PreToolUse / PostToolUse / Stop / SubagentStop / SessionStart
2. `d3` — Descoberta focada no evento: "O que o hook intercepta?", "O que faz quando disparado?", "Dê um exemplo: evento → hook faz X."
3. `intencao`, `intencao_revisao`, `nome`, `tags` — mesmo fluxo. `d4` é sempre `action` (preenchido automaticamente, sem perguntar).

**Plugin:**
- `d1`, `d2`, `intencao`, `intencao_revisao`, `nome`, `tags` — igual a Skill. Sem `d3` e `d4`.
- Preamble de `intencao`: "Descreva o problema que este plugin resolve — quais recursos ele agrupa e qual valor entrega como conjunto."

**Module:**
1. `d3` — Descoberta da capacidade: "Que capacidade este módulo entrega à skill que o adotar?", "Que parte é código determinístico e que parte exige julgamento do agente?", "Ele precisa de configuração diferente por skill?", "Ele persiste algum estado?". Encerrar quando a fronteira código/julgamento estiver clara.
2. `intencao`, `intencao_revisao`, `nome`, `tags` — mesmo fluxo de Skill. Preamble de `intencao`: "Descreva a capacidade como quem vai lê-la é o agente de outra skill, que não conhece este módulo."
3. Sem `d1`, `d2` e `d4` — módulo não é recurso de vertical nem produz output próprio; quem entrega ao usuário é a skill que o hospeda.
4. Antes de aceitar o `nome`, varrer `<raiz-de-recursos>/skills/` e `<raiz-de-recursos>/modules/` — o espaço de nomes é compartilhado, e um nome é skill **ou** módulo, nunca ambos. Colisão → rejeitar e pedir outro nome.

**Workflow:**
1. `nome` — texto livre em kebab-case. Define `.claude/agents/<nome>-workflow.md` e `.claude/agents/<nome>-workflow.mmd`.
2. `visao_geral` — conversa adaptativa: "O que este workflow faz?", "Quais são as etapas? Quem executa cada uma?", "Existem etapas condicionais ou recorrentes?", "O workflow acessa serviços externos?". Extrair `descricao`, `nodes` (id, label, type, agent/skills, output_template) e `integracoes`.
3. `schedule` — Manual / Diário (`0 8 * * *`) / Dias úteis (`0 9 * * 1-5`) / Semanal (`0 8 * * 1`) / Outro (cron expression).
4. `tags`.

### Fase 3 — Criar recurso

| Tipo | Destino | Template fonte |
|---|---|---|
| `skill` | `.claude/skills/<nome>/` | `${CLAUDE_PLUGIN_ROOT}/templates/skills/skill/` (cópia de diretório, exceto `GUIDE.md`) |
| `agent` | `.claude/agents/<nome>/` | `${CLAUDE_PLUGIN_ROOT}/templates/agents/agent.md` → `<nome>.md`, mais `agent-description.md` do mesmo diretório |
| `hook` | `.claude/hooks/<nome>/` | `hook.json` gerado + `${CLAUDE_PLUGIN_ROOT}/templates/hooks/events/<evento>.sh` → `hook.sh` (chmod 755) |
| `command` | `.claude/commands/<nome>.md` | `${CLAUDE_PLUGIN_ROOT}/templates/commands/command.md` |
| `plugin` | `.claude/plugins/<nome>.json` | `${CLAUDE_PLUGIN_ROOT}/templates/plugins/plugin.json` |
| `workflow` | `.claude/agents/<nome>-workflow.md` + `.claude/agents/<nome>-workflow.mmd` | `${CLAUDE_PLUGIN_ROOT}/templates/workflows/workflow-agent.md` |
| `module` | `.claude/modules/<nome>/` | `${CLAUDE_PLUGIN_ROOT}/templates/modules/default/` (cópia de diretório) |

Mapeamento hook_event → script: PreToolUse → `pre-tool-use.sh` | PostToolUse → `post-tool-use.sh` | Stop → `stop.sh` | SubagentStop → `subagent-stop.sh` | SessionStart → `session-start.sh`.

Cópia do template de skill exclui `GUIDE.md`: ele orienta quem cria a skill, não é arquivo interno dela. Copiá-lo poria dentro da skill gerada um arquivo com frontmatter fora do padrão de catálogo (`scripts/frontmatter/skill-frontmatter.md` §1, no repositório AmFlow).

**Ler o `GUIDE.md`, nunca apontar para ele.** Ao criar uma `skill`, ler
`${CLAUDE_PLUGIN_ROOT}/templates/skills/skill/GUIDE.md` antes de preencher o `SKILL.md` — ele traz os
quatro arquétipos, o peso de cada seção por arquétipo e os padrões de instrução A–E. O arquivo é
legível aqui, do lado do plugin; do lado do projeto não existe, porque a cópia o exclui de propósito.
Ponteiro para ele dentro da skill gerada não resolve, e ainda viaja ao Hub junto com o recurso.

Se template não encontrado → gerar arquivo com frontmatter completo e seções padrão do tipo inline.
Se recurso já existe no destino → encerrar: `Recurso já existe: <caminho> — edite-o diretamente ou use /amflow-builder:publish para publicá-lo`

**Documento de descrição.** Skill, agent e módulo nascem com um `[tipo]-description.md` na raiz da
própria pasta — `skill-description.md`, `agent-description.md`, `module-description.md`. Em skill e
módulo ele vem na cópia de diretório; em agent é copiado à parte, junto com o `<nome>.md`. É o
documento que explica o recurso a quem não o conhece, e é **obrigatório para publicar no Hub**: recurso
sem ele não passa no gate. Não preencher agora é aceitável; criar sem ele, não.

**Frontmatter — não se aplica a `skill`, que tem bloco próprio logo abaixo (`module` também, em Module extra):**

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

**Skill:** a tabela acima não se aplica — segue a norma de frontmatter
(`scripts/frontmatter/skill-frontmatter.md`, no repositório AmFlow). `d1`, `d2` e `d4` continuam
coletados no survey (Fase 2, inalterado) para orientar `nome`, `tags` e `intencao`, mas não viram
campo do frontmatter — pendentes do backlog `B-05` (`docs/plan/_inbox/_backlog.md`, no repositório
AmFlow). `type`, `created`, `project` e `source` não se aplicam: derivam da pasta, do git e do
repositório.
`amflow-version`, `amflow-status` e `amflow-dependencies` já nascem preenchidos no template — a Fase 3
não os toca.

| Campo | Valor |
|---|---|
| `name` | `nome` |
| `description` | `intencao` |
| `license` | `Proprietary` |
| `metadata.amflow-author` | `git config user.name` (local → global); vazio nos dois → perguntar o nome ao Creator. Nunca omitir a chave nem gravá-la vazia — R-07 a exige **com valor** |
| `metadata.amflow-author-id` | `<user_id>` obtido na Fase 0 — sempre preenchido (a Fase 0 garante sessão autenticada) |
| `metadata.amflow-updated` | `date +%Y-%m-%d` |
| `metadata.amflow-tags` | selecionados, separados por espaço — nunca lista |

**Module extra:** a tabela de frontmatter acima **não se aplica** — módulo não tem frontmatter. Sua identidade vive no `module.json`, com três campos: `name` (igual ao do diretório), `version` (inicial `1.0.0`) e `description` (a `intencao` coletada no survey, em uma frase terminada em ponto — a instalação a copia literalmente para a região `modules` da skill, então ela precisa ler bem fora de contexto). O `MODULE.md` é prosa, sem bloco YAML. Remover `config.example.json` do módulo gerado quando o survey indicou que ele não é configurável.

**Workflow extra:** preencher `## Definição` com nodes e edges extraídos de `visao_geral`. Gerar `<nome>-workflow.mmd` como `flowchart TD` — nós `type: human` com prefixo `👤`, back-edges com sufixo `↻` na label.

### Fase 4 — Exibir resultado

Listar arquivos criados e sugerir próximos passos:
- Editar o recurso (preencher o conteúdo específico)
- Preencher o `[tipo]-description.md` — em skill, agent e módulo. Sem ele preenchido a publicação é
  recusada, e é o texto que a página do Hub exibe a quem considera comprar
- Preencher `evals/eval_queries.json` — em skill. São os prompts que devem ativá-la e os *near-miss*
  que não devem: para uma skill, a `description` é a superfície inteira de ativação, e declarar os
  near-miss é o que expõe uma descrição larga demais. Também é exigido na publicação
- `/amflow-builder:publish` quando o recurso estiver pronto

## Restrições

- Um recurso por execução — nunca criar múltiplos em batch sem solicitação explícita.
- Nome inválido (maiúscula, espaço, hífen inicial/final, hífens consecutivos ou > 64 chars) → rejeitar e informar a regra.
- `git config user.name` vazio no local e no global → perguntar o nome do autor ao Creator e carimbar
  a resposta. Nunca omitir o campo nem gravá-lo vazio: `amflow-author` é obrigatória **com valor** na
  fonte (R-07), e o agent `reviewer` cobra o mesmo — recurso que nasce sem ela reprova na revisão e
  não publica. A tool `me` não serve de saída: devolve só o `user_id`, sem perfil.
- Nunca sobrescrever recurso existente sem confirmação explícita.

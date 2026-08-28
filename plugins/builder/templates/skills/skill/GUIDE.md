---
# about
name: skill-guide
type: doc
project: AmFlow
description: Guia de preenchimento do SKILL.md por tipo de skill — processo, contexto de projeto, ferramenta e domínio
tags: [builder, skill, template, guide]

# history
author: Bortoli
created: 2026-06-06
status: stable
version: 1.0.0
updated: 2026-06-06

# system
scope: project
auto_load: false
dependencies: []

# referências de criação
# [1] Agent Skills open standard (specification)  https://agentskills.io/specification
# [2] Claude Code — Extend Claude with skills     https://code.claude.com/docs/en/skills
---

# Guia de Preenchimento do SKILL.md por Tipo

O Agent Skills open standard não define categorias fixas. O que existe são **4 arquétipos de
conteúdo** — cada um com necessidades distintas de frontmatter e seções. Um skill real pode combinar
traços de mais de um tipo; use o arquétipo dominante como referência.

Arquétipo é o único eixo. **Não existe escolha de template.**

Havia um segundo eixo aqui — A portável × B do Claude Code —, apoiado na ideia de que declarar
extensão do Claude Code fazia o upload recusar o arquivo em Cowork, routines e claude.ai. **A medição
de 2026-08-27 e 28 desmentiu:** dez sondas, dez uploads, nenhuma recusa, com as quatorze extensões
declaradas. Ver a §4 da norma (`scripts/frontmatter/skill-frontmatter.md`, no repositório AmFlow).

Declare o campo que carrega comportamento; omita o resto. É higiene de leitura, não portabilidade.

---

## Como identificar o tipo

| Pergunta | Tipo provável |
|---|---|
| O skill ensina *como* executar um processo repetível? | Processo |
| O skill carrega contexto específico de um projeto ou organização? | Contexto de projeto |
| O skill encapsula o uso correto de uma ferramenta (API, CLI, biblioteca)? | Ferramenta |
| O skill combina processo + ferramentas + gotchas de um domínio vertical? | Domínio |

---

## O que toda skill declara, seja qual for o arquétipo

As tabelas de cada arquétipo, mais abaixo, cobrem só o que varia por tipo. Isto aqui é piso, não teto
— frontmatter e `metadata` seguem a norma do AmFlow por inteiro
(`scripts/frontmatter/skill-frontmatter.md`, no repositório AmFlow).

| Campo | Por quê |
|---|---|
| `name` | igual ao nome do diretório |
| `description` | o quê + quando — é o que decide o match, com ou sem gatilho extra |
| `license` | obrigatório no AmFlow, mesmo pra skill que nunca vai ao Hub |
| `metadata` | bloco próprio do AmFlow — dado do AmFlow nunca vai no topo |

Dentro de `metadata`, sete chaves são obrigatórias desde a criação: `amflow-version`,
`amflow-status`, `amflow-author`, `amflow-author-id`, `amflow-updated`, `amflow-tags`,
`amflow-dependencies`. `amflow-hub-id` só existe depois da 1ª publicação; `amflow-source` só na cópia
instalada — nenhuma das duas no repositório do Creator. `/amflow-builder:build` preenche o que dá pra
preencher sozinho na Fase 0/3 (autor, uuid, data); `description`, tags e o que o arquétipo pedir de
comportamento real é survey, não copy-paste do template.

**Nunca declarar campo no valor default.** `disable-model-invocation: false`, `user-invocable: true`,
`shell: bash`, `context: ""`, `model: ""` — presente e no default é ruído. Não quebra nada em destino
nenhum; é linha a mais para ler, editar e manter em dia, sem efeito. Se a tabela do arquétipo não
pedir o campo, ele fica comentado no template — descomentar é ato deliberado, não preenchimento de
formulário.

---

## Processo

*Ensina como executar um tipo de tarefa. O método generaliza, os detalhes variam.*

**Frontmatter enxuto.** Processo raramente precisa de extensão: use `effort` e `when_to_use` só
quando o comportamento exigir.

### Frontmatter

| Campo | Orientação |
|---|---|
| `description` | Descrever o workflow completo em imperativo. Ex: "Executa revisão de código antes de commit verificando lógica, nomenclatura e casos de borda." |
| `effort` | `medium` ou `high` — processos têm múltiplos passos |
| `when_to_use` | Quando acionar o processo vs. quando não acionar |

### Seções

| Seção | Peso | Orientação |
|---|---|---|
| `## Quando usar` | Alto | Gatilhos específicos — contextos em que o processo faz sentido vs. quando não faz |
| `## Não usar quando` | Alto | Situações onde o processo seria overhead ou inadequado |
| `## Gotchas` | Médio | Armadilhas comuns — onde as pessoas erram na execução |
| `## Instruções` | Principal | Padrão B (checklist sequencial) ou D (plan → validate → execute) |
| `## Output` | Alto | Template concreto do que o processo entrega (Padrão C) |
| `## Scripts` | Baixo | Apenas se a automação de passos específicos for viável |

### Padrões dominantes

- **B — Checklist**: passos sequenciais com portas de validação
- **D — Plan → validate → execute**: para processos com etapa de planejamento explícita
- **C — Template de output**: para processos com entrega padronizada

---

## Contexto de Projeto

*Carrega conhecimento específico de um projeto ou organização — esquema de banco, convenções de nomenclatura, decisões arquiteturais.*

**Use `when_to_use` à vontade.** Contexto de projeto raramente sai do repositório onde nasceu, e o
gatilho costuma ser específico demais para caber no `description`.

### Frontmatter

| Campo | Orientação |
|---|---|
| `description` | Mencionar o projeto ou domínio específico. Ex: "Carrega o esquema do banco AmFlow e as convenções de nomenclatura do projeto." A ativação é só por aqui — não existe campo que a dispense. |
| `when_to_use` | Frequentemente dispensável: a `description` de um contexto de projeto costuma já ser específica o bastante pro match sozinho. Declarar só se o gatilho real não couber nela. |

### Seções

| Seção | Peso | Orientação |
|---|---|---|
| `## Gotchas` | **Principal** | Fatos que o Claude erraria sem saber — convenções não-óbvias, exceções ao padrão, nomes enganosos |
| `## O que faz` | Médio | Descrever qual contexto o skill fornece |
| `## Instruções` | Baixo | Mínimo — foco em prover contexto, não em procedimentos |
| `## Referências` | Alto | Apontar para `references/` com schemas, decisões arquiteturais, docs internos |
| `## Quando usar` | Baixo | Cobre só o que a `description` não capturar — não existe mais campo que dispense a seção inteira |

### Padrões dominantes

- **A — Gotchas**: seção mais importante; cada gotcha deve ser um fato específico e acionável

---

## Ferramenta

*Encapsula o uso correto de uma ferramenta específica — API, biblioteca, CLI.*

**`compatibility` e `allowed-tools` são os campos que importam aqui** — é onde o requisito de
ambiente e a pré-aprovação de ferramenta se declaram. As extensões raramente acrescentam algo a um
wrapper de ferramenta.

### Frontmatter

| Campo | Orientação |
|---|---|
| `description` | Mencionar a ferramenta pelo nome. Ex: "Executa queries no Supabase via CLI — sintaxe correta, flags de ambiente e tratamento de erros." |
| `compatibility` | Nomear a ferramenta e versão requerida. Ex: "Requer supabase-cli >= 2.0 e acesso à internet." |
| `allowed-tools` | Pré-aprovar o Bash com os comandos da ferramenta |

### Seções

| Seção | Peso | Orientação |
|---|---|---|
| `## Scripts` | **Principal** | Scripts que encapsulam os quirks da ferramenta — interface correta, tratamento de erros, idempotência |
| `## Gotchas` | Alto | Flags não-óbvias, comportamentos contraintuitivos, armadilhas de versão |
| `## Instruções` | Médio | Exemplos de chamadas corretas; mencionar o que não fazer |
| `## Output` | Médio | Formato do output da ferramenta e como interpretá-lo |
| `## Referências` | Alto | Doc oficial da ferramenta em `references/` |
| `## Quando usar` | Baixo | Geralmente óbvio pelo nome — manter conciso |

### Padrões dominantes

- **A — Gotchas**: quirks, flags obscuras, armadilhas de versão
- **Scripts**: encapsulam a interface correta sem poluir o contexto

---

## Domínio

*Expertise vertical — combina processo + ferramentas + gotchas de um domínio específico (engenharia de dados, revisão jurídica, análise financeira).*

**Frontmatter enxuto**, mesma lógica de Processo: a expertise está no corpo, não no topo.

### Frontmatter

| Campo | Orientação |
|---|---|
| `description` | Mencionar o domínio vertical e a tarefa. Ex: "Conduz análise de risco financeiro seguindo IFRS 9 — inclui checklist de provisões e validação de exposição." |
| `d1` / `d2` | **Suspenso.** Não são da spec, não são extensão do Claude Code, não estão definidos na norma — pendente do backlog B-05. Não preencher no frontmatter |
| `effort` | `high` ou `max` — domínios envolvem raciocínio especializado |

### Seções

| Seção | Peso | Orientação |
|---|---|---|
| `## Quando usar` | **Principal** | Crucial — domínios são ativados por contextos implícitos; ser específico evita falsos positivos |
| `## Não usar quando` | Alto | Delimitar o escopo do domínio — o que está fora |
| `## Gotchas` | Alto | O que um não-especialista erraria; normas contraintuitivas; exceções ao padrão do domínio |
| `## Instruções` | Alto | Combinação de padrões conforme a tarefa do domínio |
| `## Referências` | Alto | Normas, regulações, padrões do domínio em `references/` |
| `## Output` | Médio | Formato específico exigido pelo domínio (relatório regulatório, parecer jurídico, etc.) |

### Padrões dominantes

- Todos (A, B, C, D) conforme a tarefa específica do domínio
- Calibração (Padrão E) é especialmente relevante — domínios exigem julgamento, não só regras

---

## Referência de Padrões de Instrução

| Padrão | Nome | Quando usar |
|---|---|---|
| A | Gotchas | Fatos específicos do ambiente que o agente erraria sem ser informado |
| B | Checklists e validation loops | Tarefas com dependências sequenciais ou portas de validação |
| C | Templates de output | Entregas com formato fixo e previsível |
| D | Plan → validate → execute | Processos com etapa de planejamento antes da execução |
| E | Calibração | Quando o grau de prescrição vs. liberdade precisa ser definido explicitamente |

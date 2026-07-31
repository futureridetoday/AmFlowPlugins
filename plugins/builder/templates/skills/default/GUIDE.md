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
# [3] Guia de Categorização de Agent Skills       docs/mvp/40_reference/agent-skills-category.html
---

# Guia de Preenchimento do SKILL.md por Tipo

O Agent Skills open standard não define categorias fixas. O que existe são **4 arquétipos por escopo de distribuição** — cada um com necessidades distintas de frontmatter e seções. Um skill real pode combinar traços de mais de um tipo; use o arquétipo dominante como referência.

---

## Como identificar o tipo

| Pergunta | Tipo provável |
|---|---|
| O skill ensina *como* executar um processo repetível? | Processo |
| O skill carrega contexto específico de um projeto ou organização? | Contexto de projeto |
| O skill encapsula o uso correto de uma ferramenta (API, CLI, biblioteca)? | Ferramenta |
| O skill combina processo + ferramentas + gotchas de um domínio vertical? | Domínio |

---

## Processo

*Ensina como executar um tipo de tarefa. O método generaliza, os detalhes variam.*

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

### Frontmatter

| Campo | Orientação |
|---|---|
| `description` | Mencionar o projeto ou domínio específico. Ex: "Carrega o esquema do banco AmFlow e as convenções de nomenclatura do projeto." |
| `scope` | `project` — raramente publicável no marketplace público |
| `auto_load` | Considerar `true` — o contexto é geralmente sempre relevante |
| `when_to_use` | Omitir ou manter mínimo — `auto_load: true` dispensa gatilho explícito |

### Seções

| Seção | Peso | Orientação |
|---|---|---|
| `## Gotchas` | **Principal** | Fatos que o Claude erraria sem saber — convenções não-óbvias, exceções ao padrão, nomes enganosos |
| `## O que faz` | Médio | Descrever qual contexto o skill fornece |
| `## Instruções` | Baixo | Mínimo — foco em prover contexto, não em procedimentos |
| `## Referências` | Alto | Apontar para `references/` com schemas, decisões arquiteturais, docs internos |
| `## Quando usar` | Baixo | Omitir se `auto_load: true` |

### Padrões dominantes

- **A — Gotchas**: seção mais importante; cada gotcha deve ser um fato específico e acionável

---

## Ferramenta

*Encapsula o uso correto de uma ferramenta específica — API, biblioteca, CLI.*

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

### Frontmatter

| Campo | Orientação |
|---|---|
| `description` | Mencionar o domínio vertical e a tarefa. Ex: "Conduz análise de risco financeiro seguindo IFRS 9 — inclui checklist de provisões e validação de exposição." |
| `d1` / `d2` | Preencher com a vertical e função correspondentes |
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

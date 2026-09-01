# Arquétipos de skill

O Agent Skills open standard não define categorias fixas. Existem quatro **arquétipos de
conteúdo** — cada um pede um frontmatter e um peso de seção diferentes. Uma skill real pode
combinar traços de mais de um; use o arquétipo dominante como referência, não como categoria
exclusiva.

## Como identificar o arquétipo

| Pergunta | Arquétipo provável |
|---|---|
| Ensina *como* executar um processo repetível? | Processo |
| Carrega conhecimento específico de um projeto ou organização? | Contexto de projeto |
| Encapsula o uso correto de uma ferramenta (API, CLI, biblioteca)? | Ferramenta |
| Combina processo + ferramentas + gotchas de um domínio vertical? | Domínio |

## Processo

Ensina como executar um tipo de tarefa — o método generaliza, os detalhes variam.

| Seção | Peso | Orientação |
|---|---|---|
| `## Quando usar` | Alto | Gatilhos específicos — quando o processo faz sentido e quando não |
| `## Não usar quando` | Alto | Onde o processo seria overhead ou inadequado |
| `## Gotchas` | Médio | Armadilhas comuns na execução |
| `## Instruções` | Principal | Padrão B (checklist) ou D (plan → validate → execute) |
| `## Output` | Alto | Template concreto do que o processo entrega (Padrão C) |

## Contexto de projeto

Carrega conhecimento específico de um projeto — esquema, convenções, decisões arquiteturais.

| Seção | Peso | Orientação |
|---|---|---|
| `## Gotchas` | **Principal** | Fatos que o Claude erraria sem saber — convenções não-óbvias, exceções, nomes enganosos |
| `## O que faz` | Médio | Que contexto a skill fornece |
| `## Referências` | Alto | Apontar para `references/` com schemas e docs internos |
| `## Instruções` | Baixo | Mínimo — o foco é prover contexto, não procedimento |

Esta própria skill é uma instância do arquétipo: `## Gotchas` é a seção principal do `SKILL.md`, e
as duas referências ao lado carregam o resto.

## Ferramenta

Encapsula o uso correto de uma ferramenta específica.

| Seção | Peso | Orientação |
|---|---|---|
| `## Scripts` | **Principal** | Scripts que encapsulam os quirks — interface correta, idempotência |
| `## Gotchas` | Alto | Flags não-óbvias, comportamentos contraintuitivos, armadilhas de versão |
| `## Instruções` | Médio | Exemplos de chamada correta; o que não fazer |
| `## Referências` | Alto | Doc oficial da ferramenta em `references/` |

## Domínio

Expertise vertical — processo + ferramentas + gotchas de um domínio específico.

| Seção | Peso | Orientação |
|---|---|---|
| `## Quando usar` | **Principal** | Domínios ativam por contexto implícito — ser específico evita falso positivo |
| `## Não usar quando` | Alto | Delimitar o que está fora do domínio |
| `## Gotchas` | Alto | O que um não-especialista erraria |
| `## Instruções` | Alto | Combinação de padrões conforme a tarefa |
| `## Referências` | Alto | Normas e padrões do domínio em `references/` |

## Padrões de instrução

| Padrão | Nome | Quando usar |
|---|---|---|
| A | Gotchas | Fatos específicos do ambiente que o agente erraria sem ser informado |
| B | Checklists e validation loops | Tarefas com dependências sequenciais ou portas de validação |
| C | Templates de output | Entregas com formato fixo e previsível |
| D | Plan → validate → execute | Processos com etapa de planejamento antes da execução |
| E | Calibração | Quando o grau de prescrição vs. liberdade precisa ser definido explicitamente |

## O piso, para qualquer arquétipo

| Campo | Por quê |
|---|---|
| `name` | igual ao nome do diretório |
| `description` | o quê + quando — decide o match |
| `license` | obrigatório no AmFlow, mesmo para skill que nunca vai ao Hub |
| `metadata` | bloco próprio do AmFlow — ver [`frontmatter.md`](frontmatter.md) |

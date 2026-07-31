---
# about
name: hard-memory
type: skill
project: AmFlow
description: Protocolo de memória persistente por arquivo para agents — leitura no início da sessão, escrita após cada tarefa e compactação por threshold de linhas
tags: [hard-memory, memory, persistence, agent, infrastructure]

# history
author: Bortoli
created: 2026-06-12
status: stable
version: 1.0.0
updated: ""

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# Hard Memory

Protocolo de memória persistente por arquivo para agents AmFlow. Skill de infraestrutura — instalada automaticamente com o plugin, não adquirível no Hub. Invocada por agents com `hard_memory.enabled: true` no frontmatter.

## Configuração do agent

O agent declara no frontmatter:

```yaml
hard_memory:
  enabled: true
  scope: project              # project | global
  strategy: rewrite           # rewrite | append
  compaction_threshold: 80    # linhas — acima disso, compactar antes de escrever
```

## Paths

| Scope | Arquivo de memória |
|---|---|
| `project` | `.claude/hard-memory/<nome-do-agent>.md` (relativo ao projeto atual) |
| `global` | `~/.claude/hard-memory/<nome-do-agent>.md` |

Archive (auditoria, nunca lido automaticamente): mesmo diretório, sufixo `.archive.md`.

## Schema do arquivo de memória

```markdown
---
agent: <agent-name>
updated: <YYYY-MM-DD HH:MM>
sessions: <n>
---

## Contexto do Projeto
## Preferências do Usuário
## Estado de Tarefas
## Decisões Registradas
## Aprendizados
```

**O que persiste:** preferências observadas do usuário, decisões e rationale, padrões do projeto, estado de tarefas em andamento, erros cometidos e como evitá-los.

**O que não persiste:** conteúdo de arquivos do projeto, resultados intermediários de ferramentas, informações recuperáveis via git ou Read, contexto óbvio e estável.

## Protocolo de leitura

Executar no início de cada sessão, antes de qualquer tarefa:

1. Verificar se o arquivo de memória existe no path configurado.
   - Existe → ler com a ferramenta Read e usar o conteúdo como contexto da sessão.
   - Não existe → prosseguir sem contexto anterior (o arquivo será criado na primeira escrita).

## Protocolo de escrita

Executar após cada tarefa concluída — não apenas ao encerrar a sessão:

1. Checar o número de linhas do arquivo atual (`wc -l`).
2. Se linhas > `compaction_threshold` → executar o protocolo de compactação antes de escrever.
3. Consolidar o estado atual nas seções do schema — sem duplicar entradas existentes.
4. Reescrever o arquivo completo com a ferramenta Write (strategy `rewrite`) ou acrescentar entrada com timestamp (strategy `append`).
5. Atualizar o frontmatter: `updated` com data/hora atual e `sessions` incrementado em 1 por sessão (não por escrita).

## Protocolo de compactação

Disparado quando o arquivo ultrapassa `compaction_threshold` linhas (apenas strategy `rewrite`):

1. Copiar o conteúdo atual para `<nome>.archive.md` no mesmo diretório — append ao final, com separador `## Sessão <n> — <data>`.
2. Consolidar as seções: mesclar entradas redundantes, sumarizar histórico em estado atual.
3. Escrever o arquivo compactado no path principal.

O `.archive.md` existe apenas para auditoria manual pelo usuário — nunca é lido automaticamente.

## Limitações conhecidas

- O arquivo é lido inteiro a cada sessão — sem disciplina no que persiste, consome contexto significativo.
- Sessões paralelas do mesmo agent: a última escrita vence; não há merge.
- Se esta skill não estiver instalada, o agent deve degradar graciosamente e prosseguir sem memória.

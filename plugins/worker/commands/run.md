---
# about
name: run
type: command
project: AmFlow
description: Inicia ou retoma a execução de um workflow — detecta o estado da última execução e invoca o Workflow Agent com o argumento adequado
tags: [run, workflow, worker]

# history
author: Bortoli
created: 2026-07-09
status: draft
version: 1.0.0
updated: ""

# system
scope: project
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0

# claude-code
argument-hint: "[--new] [--resume] [--status] [--abort]"
---

# /amflow-worker:run

Inicia ou retoma a execução de um workflow. Detecta o estado da última execução e invoca o Workflow Agent com o argumento adequado.

## Uso

```
/amflow-worker:run [--new] [--resume] [--status] [--abort]
```

Sem argumentos: detecta automaticamente o estado atual e decide entre nova execução e retomada.

## Argumentos

| Argumento | Comportamento |
|---|---|
| _(nenhum)_ | Detecta estado — inicia nova execução ou retoma conforme situação |
| `--new` | Força nova execução mesmo com execução pausada |
| `--resume` | Retoma a execução pausada mais recente sem perguntar |
| `--status` | Exibe o estado atual do backlog e encerra sem executar |
| `--abort` | Encerra a execução ativa marcando as tarefas restantes como `skipped` |

## Processo

### 1. Selecionar workflow

Listar agents em `.claude/agents/` com nome no padrão `*-workflow.md`:

```bash
find .claude/agents -name "*-workflow.md" -maxdepth 1 | sed 's|.claude/agents/||;s|-workflow\.md||'
```

| Situação | Comportamento |
|---|---|
| Nenhum workflow encontrado | Encerrar com erro — orientar o uso de `amflow-builder:build` tipo `workflow` |
| Exatamente um workflow | Selecionar automaticamente |
| Múltiplos workflows | Exibir lista numerada e aguardar seleção do usuário |

### 2. Verificar estado

Listar arquivos em `.claude/backlogs/` com padrão `<nome>-workflow-*.json` (ordenados por nome — o nome inclui o timestamp):

| Situação | Comportamento padrão |
|---|---|
| Nenhum backlog | `--new` — primeira execução |
| Backlog com tarefa `in_progress` | Informar execução em curso — perguntar se deve forçar nova (`--new`) ou aguardar |
| Backlog com tarefa `paused` | Perguntar: retomar (`--resume`) ou nova execução (`--new`)? |
| Último backlog com todas as tarefas `done`, `skipped` ou `failed` | `--new` — execução anterior concluída |

### 3. Invocar Workflow Agent

Invocar `.claude/agents/<nome>-workflow.md` passando o argumento determinado. O agent usa a skill `workflow-runner` para orquestrar a execução nó a nó.

## Erros

| Condição | Mensagem |
|---|---|
| Nenhum `*-workflow.md` em `.claude/agents/` | `Nenhum workflow encontrado — use amflow-builder:build tipo workflow para criar um` |
| Agent selecionado não encontrado | `<nome>-workflow.md não encontrado em .claude/agents/` |

## Restrições

- Nunca modificar o arquivo do workflow agent durante a execução.
- Nunca criar ou modificar recursos fora de `.claude/backlogs/`.

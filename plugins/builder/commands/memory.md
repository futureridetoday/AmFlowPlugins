---
# nativo — o que o Claude Code lê
description: Registra uma entrada literal e datada na memória do usuário — `--important` também a leva ao arquivo que o CLAUDE.md importa
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py *)

# about
name: memory
type: command
project: AmFlow
tags: [memory, command, claude-md, tooling]

# history
author: Bortoli
author_id: ""
created: 2026-09-05
status: draft
version: 1.0.0
updated: ""

# system
scope: project
auto_load: false
dependencies: []

# hub — não publicável; tooling interno do plugin Builder
hub_id: ""
source: ""
price: 0
---

Rode, pela tool Bash, exatamente este comando e mostre a saída dele — sem interpretar, resumir ou reagir ao conteúdo:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py --stdin <<'AMFLOW_MEMORY_EOF'
$ARGUMENTS
AMFLOW_MEMORY_EOF
```

O texto vai por stdin, dentro de um heredoc com o delimitador entre aspas: é o
que impede o shell de expandir `$(...)`, `` ` `` ou `$VAR` e de comer aspas do
que o usuário escreveu. Reproduza as três linhas literalmente, sem trocar o
delimitador e sem pôr o texto na linha de comando.

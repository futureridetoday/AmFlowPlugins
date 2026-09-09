---
# nativo — o que o Claude Code lê
description: Registra uma entrada literal e datada na memória do usuário — `--important` também a leva ao arquivo que o CLAUDE.md importa
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py *)

# about
name: memory
type: command
project: AmFlow
tags: [memory, command, claude-md, tooling, worker]

# history
author: Bortoli
created: 2026-09-09
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
---

Rode, pela tool Bash, exatamente este comando e mostre a saída dele — sem interpretar, resumir ou reagir ao conteúdo:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py -- "$ARGUMENTS"
```

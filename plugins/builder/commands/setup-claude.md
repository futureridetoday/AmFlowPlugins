---
# about
name: setup-claude
type: command
project: AmFlow
description: Configura o CLAUDE.md do projeto atual — invoca a skill setup-claude
tags: [setup, claude-md, config, creator]

# history
author: Bortoli
created: 2026-06-14
status: stable
version: 1.1.0
updated: 2026-07-11

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-builder:setup-claude

Configura ou atualiza o `CLAUDE.md` do projeto atual via perguntas guiadas.

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow`.

- Sucesso → guarde o `user_id` retornado para carimbar `author_id` no `CLAUDE.md` gerado. Com sessão já ativa, o `me` responde direto e o comando segue sem novo login.
- Sem sessão / erro → o conector `amflow` não está autorizado nesta sessão. **Encerre aqui** — não gere nem altere arquivo. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

## Processo

1. Execute a skill `setup-claude` no projeto atual (diretório retornado por `pwd`), passando o `user_id` da Fase 0 para gravar `author_id` no frontmatter.

## Restrições

- Exige sessão AmFlow autenticada (Fase 0) — reversão da isenção anterior (decisão 1A do plano `login-por-comando-builder-e-atribuicao`).
- Toda a lógica de coleta e geração do `CLAUDE.md` está na skill `setup-claude`.

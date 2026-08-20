---
# about
name: describe
type: command
project: AmFlow
description: Explica um recurso da autoria do Creator a partir do documento de descrição dele — invoca a skill describe-resource
tags: [creator, documentacao, recurso, description]

# history
author: Bortoli
created: 2026-08-20
status: draft
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

# /amflow-builder:describe

Explica um recurso do projeto — skill, agent ou módulo — a partir do `[tipo]-description.md` dele.

**Sem Fase 0.** Este comando não chama o MCP: é leitura de disco, sem rede e sem autenticação.

## Processo

Carregue a skill `describe-resource` e siga as instruções dela.

O argumento, quando houver, é o recurso e a pergunta — `/amflow-builder:describe como usar a skill
frontmatter-check`. Sem argumento, pergunte sobre qual recurso o Creator quer saber, listando o que
existe no projeto.

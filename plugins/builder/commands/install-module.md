---
# about
name: install-module
type: command
project: AmFlow
description: Instala um módulo numa skill, ou propaga uma nova versão de módulo para todas as skills que o consomem
tags: [module, install, update, propagate, skill, creator]

# history
author: Bortoli
created: 2026-08-14
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

# /amflow-builder:install-module

Instala um módulo numa skill, ou propaga uma nova versão para quem já o consome. As duas são a mesma operação — propagar é instalar de novo, em cada consumidor.

Invoca a skill `install-module`, que é onde o procedimento e os invariantes vivem. Este comando só resolve o alvo e escolhe a operação.

## Fase 1 — Alvo

1. Identificar o projeto:
   - Executar `pwd` → exibir o caminho atual como sugestão. Aceitar "Informar outro caminho".
   - Validar que o caminho contém `.claude/CLAUDE.md` → ausente, encerrar: **"Projeto não encontrado em: <caminho> — verifique se o diretório contém .claude/CLAUDE.md"**

2. Listar os módulos disponíveis em `<raiz-de-recursos>/modules/` com nome e versão lidos de cada `module.json`.
   - Nenhum módulo → encerrar: **"Nenhum módulo neste projeto — crie um com /amflow-builder:build, tipo module"**

3. Perguntar qual módulo.

## Fase 2 — Operação

Perguntar o que fazer, exibindo o estado atual como contexto — quais skills já consomem o módulo, e em que versão:

| Operação | Quando |
|---|---|
| `instalar` | Adicionar o módulo a uma skill que ainda não o tem |
| `propagar` | Levar a versão da origem a todas as skills que já o consomem |

Se nenhuma skill consome o módulo ainda, `propagar` não é oferecida.

**Instalar** → listar as skills sob `<raiz-de-recursos>/skills/` que ainda **não** têm `amflow.module.<nome>` em `metadata`, e perguntar em qual instalar.

**Propagar** → confirmar a lista de consumidores e a transição de versão antes de escrever qualquer coisa. É a operação que apaga e recopia em vários lugares de uma vez; o Creator vê o alcance antes.

## Fase 3 — Executar

Seguir a skill `install-module` — seção **Instruções**, e os **Invariantes** sem exceção.

Não reimplemente a sequência aqui. Se este comando e a skill divergirem, a skill manda: é onde o procedimento vive, e é ela que o Claude também carrega quando o Creator não usa o comando.

## Fase 4 — Exibir resultado

O formato está em **Output** na skill. Ao final, lembrar que:

- A cópia em `<skill>/modules/<nome>/` é gerada — editar ali é perdido na próxima propagação.
- Mudanças de comportamento vão para a origem, em `<raiz-de-recursos>/modules/<nome>/`.
- `<skill>/config/<nome>.json` é da skill e sobrevive.

## Restrições

- Um módulo por execução.
- Nunca criar módulo — origem inexistente encerra e aponta `/amflow-builder:build`.
- Propagar exige confirmação explícita: apaga e recopia em vários consumidores.

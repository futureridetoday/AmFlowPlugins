---
# about
name: planos
type: doc
project: AmFlowPlugins
description: Registro dos planos aprovados para desenvolvimento — fonte da numeração sequencial e da situação de cada plano
tags: [plan, registro, dev-units]

# history
author: Bortoli
created: 2026-08-01
status: draft
version: 1.0.0
updated: ""

# system
scope: project
auto_load: false
dependencies: []
---

# Planos aprovados

Registro dos planos que entraram em desenvolvimento. Planos no `_inbox/` **não aparecem aqui** — só
entram na aprovação, momento em que recebem o número.

Este arquivo é a **fonte da numeração**: o script lê o maior número em uso e toma o próximo.

<!-- planos:start -->
| # | Plano | Core | Módulo | Origem | Situação | Aprovado |
|---|---|---|---|---|---|---|
<!-- planos:end -->

> A **situação** é projetada a partir do estado das unidades — `em desenvolvimento` enquanto houver
> unidade fora de `verified`, `concluído` quando todas estiverem. Não editar à mão: o conteúdo entre
> os marcadores é substituído pelo script a cada projeção.

**Origem** registra qual unidade de qual plano gerou este — no formato `unit_id` (ex.: `0003-02`).
Fica vazia em planos que nascem direto no `_inbox`, sem plano-pai. É o que torna visível a hierarquia
quando um plano de core gera planos de módulo através de unidades `plan`.

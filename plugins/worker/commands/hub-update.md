---
# about
name: hub-update
type: command
project: AmFlow
description: Aplica atualizações disponíveis nos recursos AmFlow instalados, após confirmação do usuário
tags: [updates, install, worker, mcp]

# history
author: Bortoli
created: 2026-06-12
status: stable
version: 2.0.0
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

# /amflow-worker:hub-update

Aplica atualizações nos recursos instalados em `~/.claude/`, após confirmação do usuário. Atua apenas sobre `update_available` — recursos `unlicensed` são exibidos com aviso, mas nunca atualizados nem removidos. Usa as tools `check_updates` e `update` do servidor MCP `amflow-worker`.

## Processo

1. Verifique as atualizações — mesma coleta e consulta do [`/amflow-worker:hub-check`](hub-check.md):

   - Colete `name`, `type`, `version` do frontmatter dos recursos instalados em `~/.claude/` (`skills/*/SKILL.md`, `agents/*.md`, `commands/*.md`, `hooks/*/*.md`).
   - Chame a tool `check_updates({ installed: [...] })` (máximo de 200 itens por lote).

2. **Confirmação humana (M10) — obrigatória, não pule.** Exiba a lista de recursos com `update_available` (nome, versão instalada → versão nova, changelog) e use `AskUserQuestion`: **"Aplicar atualizações"** ou **"Cancelar"**.
   - Sem itens `update_available` → encerre com **"Nenhuma atualização disponível."**
   - Itens `unlicensed` → exiba **"`<name>`: licença expirada ou revogada — `<hub_url>`"** e ignore-os na atualização.
   - Só prossiga para o passo 3 após confirmação explícita.

3. Após a confirmação, para cada recurso com `update_available`, chame a tool `update`:

   ```
   update({ type: "<type>", name: "<name>", scope: "global" })
   ```

   Resposta: `{name, type, version, files, dependencies}`.

4. Aplique cada resultado:
   - Para cada entrada em `files`, sobrescreva o conteúdo com a ferramenta Write em `~/.claude/<path sem o prefixo .claude/>` (o hook de path-safety valida cada path automaticamente).
   - Falha em um recurso (erro da tool) → registre, continue os demais e reporte ao final. Status da telemetria nesse caso: `partial`.

5. Exiba o resumo: **"X recursos atualizados."** (acrescente os que falharam, se houver).

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível verificar atualizações. Tente novamente mais tarde."**

## Restrições

- Nunca exiba tokens ao usuário.
- Nunca atualize sem a confirmação do passo 2.
- Nunca escreva arquivos fora de `~/.claude/` — reforçado pelo hook de path-safety.

---
# about
name: hub-check
type: command
project: AmFlow
description: Verifica atualizações disponíveis para os recursos AmFlow instalados — apenas informa, não instala
tags: [updates, check, worker, mcp]

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

# /amflow-worker:hub-check

Verifica atualizações para os recursos instalados em `~/.claude/`. Não instala nada — apenas informa. Recursos sem licença ativa são exibidos com aviso, mas não removidos. Usa a tool `check_updates` do servidor MCP `amflow`.

## Processo

1. Colete os recursos instalados, lendo o frontmatter YAML de cada arquivo de recurso em `~/.claude/`:

   - Skills: `~/.claude/skills/*/SKILL.md`
   - Agents: `~/.claude/agents/*.md`
   - Commands: `~/.claude/commands/*.md`
   - Hooks: `~/.claude/hooks/*/*.md`

   De cada frontmatter, extraia `name`, `type` e `version`. Ignore arquivos sem esses três campos. Recursos de outras fontes que não existam no Hub são omitidos da resposta automaticamente — incluí-los é inofensivo.

   Se nenhum recurso for encontrado → informe **"Nenhum recurso AmFlow instalado."** e vá ao passo 4.

2. Chame a tool `check_updates` (máximo de 200 itens por chamada — particione em lotes e consolide se houver mais):

   ```
   check_updates({ installed: [{ type: "...", name: "...", version: "..." }, ...] })
   ```

   Resposta: `{ items: [{ name, type, status, hub_url?, installed_version?, latest_version?, changelog? }] }`.

3. Exiba o resultado para cada item da resposta:
   - `status: update_available` → **"`<name>` (`<type>`): v`<installed_version>` → v`<latest_version>` — `<changelog>`"** (omita o changelog se ausente).
   - `status: unlicensed` → **"`<name>`: licença expirada ou revogada — `<hub_url>`"**.
   - Array vazio → **"Todos os recursos estão atualizados."**

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível verificar atualizações. Tente novamente mais tarde."**
- Mais de 200 itens → particione em lotes de 200 e consolide os resultados.

## Restrições

- Nunca exiba tokens ao usuário.
- Não instale, atualize ou remova nenhum arquivo — este command é somente leitura.

---
# about
name: sync
type: command
project: AmFlow
description: Sincroniza todos os recursos com licença ativa do usuário, instalando ou sobrescrevendo em ~/.claude/
tags: [sync, install, licenses, worker, mcp]

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

# /amflow-worker:sync

Sincroniza todos os recursos com licença ativa — públicos adquiridos e exclusivos atribuídos. Instala em escopo global (`~/.claude/`), disponível em todos os projetos. Recursos instalados por outras fontes (git, cópia manual) não são tocados. Usa as tools `list_active_licenses` e `install` do servidor MCP `amflow`.

## Processo

1. Chame a tool `list_active_licenses` (sem argumentos). Resposta: `{ items: [{ name, type, version, visibility }] }`.

   Array vazio → informe **"Nenhum recurso licenciado para sincronizar."** e vá ao passo 6.

2. **Confirmação humana (M10) — obrigatória, não pule.** Exiba a lista de recursos retornados (`<type>/<name>`) e use `AskUserQuestion`: **"Sincronizar N recursos"** ou **"Cancelar"**. Só prossiga para o passo 3 após confirmação explícita — uma confirmação cobre o lote inteiro (não pergunte recurso por recurso).

3. Para cada recurso da lista, chame a tool `install`:

   ```
   install({ type: "<type>", name: "<name>", scope: "global" })
   ```

   Resposta: `{name, type, version, files, dependencies}`.

4. Aplique cada resultado:
   - Para cada entrada em `files`, escreva o conteúdo com a ferramenta Write em `~/.claude/<path sem o prefixo .claude/>` (o hook de path-safety valida cada path automaticamente). Sobrescreva se já existir.
   - Arquivos cujo nome termine em `hook.sh` → `chmod 755`.
   - Falha em um recurso (erro da tool) → registre a falha, continue os demais. Status da telemetria nesse caso: `partial`.

5. Exiba o resumo: **"X recursos sincronizados."** (acrescente os que falharam, se houver).

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Hub indisponível. Os recursos instalados localmente continuam funcionando."**

## Restrições

- Nunca exiba tokens ao usuário.
- Nunca escreva arquivos fora de `~/.claude/` — reforçado pelo hook de path-safety.
- Nunca chame `Write` pra nenhum recurso antes de completar o passo 2 (confirmação do lote).

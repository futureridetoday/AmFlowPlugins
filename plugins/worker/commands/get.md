---
# about
name: get
type: command
project: AmFlow
description: Instala um recurso específico do marketplace por tipo e nome, resolvendo licença e dependências via MCP
tags: [get, licenses, worker, mcp]

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

# claude-code
argument-hint: <type>/<name>
---

# /amflow-worker:get

Instala um recurso específico por nome. Exemplo: `/amflow-worker:get skill/deep-research`. Instala em escopo global (`~/.claude/`), disponível em todos os projetos — distinto do [`install`](install.md), que instala em projeto. Usa a tool `install` do servidor MCP `amflow` com `scope: "global"` (declarado em `.mcp.json`) — sem `curl`/Bash, sem token no contexto do modelo.

Argumento recebido: `$ARGUMENTS` — formato esperado `<type>/<name>` com `type` ∈ `skill | agent | command | hook`. Se ausente ou fora do formato, pergunte ao usuário qual recurso instalar.

## Processo

1. Chame a tool `install` do servidor MCP `amflow`:

   ```
   install({ type: "<type>", name: "<name>", scope: "global" })
   ```

   - Erro de licença → encerre exibindo a mensagem retornada pela tool, complementando com **"Adquira em: `https://dev.amflow.work/resources/<type>/<name>`"** quando for falta de licença.
   - Erro de dependência bloqueada → encerre exibindo a mensagem retornada.
   - Sucesso → prossiga com `{name, type, version, files, dependencies}`.

2. **Confirmação humana (M10) — obrigatória, não pule.** Exiba a lista de arquivos que serão escritos e as dependências incluídas, se houver. Use `AskUserQuestion`: **"Confirmar instalação"** ou **"Cancelar"**. Só prossiga para o passo 3 após confirmação explícita.

3. Para cada entrada em `files`, escreva o conteúdo com a ferramenta Write em `~/.claude/<path sem o prefixo .claude/>`. O hook de path-safety do Worker valida cada path automaticamente antes da escrita. Sobrescreva se já existir.

4. Para todo arquivo escrito cujo nome termine em `hook.sh`, ajuste a permissão de execução:

   ```bash
   chmod 755 "~/.claude/<path-do-hook.sh>"
   ```

5. Confirme: **"Recurso '`<name>`' instalado."** — inclua as dependências instaladas junto, se houver.

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível conectar ao AmFlow. Tente novamente mais tarde."**

## Restrições

- Nunca exiba tokens ao usuário.
- Nunca escreva arquivos fora de `~/.claude/` — reforçado pelo hook de path-safety.
- Nunca chame `Write` antes de completar o passo 2 (confirmação).

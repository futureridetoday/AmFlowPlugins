---
# about
name: install
type: command
project: AmFlow
description: Instala um recurso adquirido no Hub em um projeto específico — resolve licença e dependências via MCP e escreve os arquivos em <projeto>/.claude/
tags: [install, licenses, worker, project, mcp]

# history
author: Bortoli
created: 2026-07-09
status: draft
version: 2.0.0
updated: 2026-07-11

# system
scope: project
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0

# claude-code
argument-hint: <type>/<name>
---

# /amflow-worker:install

Instala um recurso adquirido no Hub em um projeto específico — diferente do [`get`](get.md), que instala em escopo global (`~/.claude/`). Usa a tool `install` do servidor MCP `amflow-worker` (declarado em `.mcp.json`) — sem `curl`/Bash, sem token no contexto do modelo. Autenticação via OAuth do `/mcp` (M3), cuidada pelo próprio Claude Code na primeira chamada.

Argumento recebido: `$ARGUMENTS` — formato esperado `<type>/<name>` com `type` ∈ `skill | agent | command | hook`. Se ausente ou fora do formato, pergunte ao usuário qual recurso instalar.

## Processo

1. **Seleção do projeto.** Execute `pwd` e use `AskUserQuestion` com 2 opções:
   - **"Usar `<caminho retornado>`"** — confirma o diretório atual como destino
   - **"Informar outro caminho"** — solicita o caminho em texto livre

   Valide que `<caminho>/.claude/CLAUDE.md` existe:
   ```bash
   test -f "<caminho>/.claude/CLAUDE.md"
   ```
   Se não existir: **"Projeto não encontrado em: `<caminho>` — verifique se o diretório contém `.claude/CLAUDE.md`."** — repita a pergunta. Guarde como `<projeto>`.

2. **Verificação local.** Antes de chamar a tool, verifique se o recurso já está instalado em `<projeto>`:

   | Tipo | Caminho |
   |---|---|
   | `skill` | `<projeto>/.claude/skills/<name>/` |
   | `agent` | `<projeto>/.claude/agents/<name>.md` |
   | `hook` | `<projeto>/.claude/hooks/<name>/` |
   | `command` | `<projeto>/.claude/commands/<name>.md` |

   Encontrado → leia `source:` do arquivo pra extrair a versão instalada e use `AskUserQuestion`: **"Manter versão atual"** (encerra) ou **"Verificar atualização"** (prossegue). Não encontrado → prossiga direto.

3. Chame a tool `install` do servidor MCP `amflow-worker`:

   ```
   install({ type: "<type>", name: "<name>", scope: "project" })
   ```

   - Erro de licença ("Recurso não encontrado."/"Licença ativa necessária...") → encerre exibindo a mensagem retornada pela tool.
   - Erro de dependência bloqueada ("Dependências bloqueadas — ...") → encerre exibindo a mensagem — já lista quais dependências e por quê (sem licença ou não encontradas no Hub).
   - Sucesso → prossiga com `{name, type, version, files, dependencies}`.

4. **Confirmação humana (M10) — obrigatória, não pule.** Exiba ao usuário a lista de arquivos que serão escritos (de `files`) e as dependências incluídas, se houver (`dependencies`). Use `AskUserQuestion`: **"Confirmar instalação"** ou **"Cancelar"**. Só prossiga para o passo 5 após confirmação explícita — cancelar encerra sem escrever nada.

5. Para cada entrada em `files`, escreva o conteúdo com a ferramenta Write em `<projeto>/<path>` (o path já vem prefixado com `.claude/`). O hook de path-safety do Worker valida cada path automaticamente antes da escrita — rejeição aqui não deveria acontecer (o servidor já valida), mas se ocorrer, é a barreira determinística funcionando, não um bug do command. Sobrescreva se já existir.

6. Para todo arquivo escrito cujo nome termine em `hook.sh`, ajuste a permissão de execução (a ferramenta Write não seta o bit):

   ```bash
   chmod 755 "<projeto>/<path-do-hook.sh>"
   ```

7. Confirme: **"Recurso '`<name>`' instalado em `<projeto>`."** — inclua as dependências instaladas junto, se houver.

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível conectar ao AmFlow. Tente novamente mais tarde."**

## Restrições

- Nunca exiba tokens ao usuário — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.
- Nunca escreva arquivos fora de `<projeto>/.claude/` — reforçado pelo hook de path-safety.
- Nunca chame `Write` antes de completar o passo 4 (confirmação).

## Fora de escopo

- **Tipo `plugin`** — `resources.type` no Hub só aceita `skill|agent|hook|command` (`CHECK` constraint); recurso `plugin` nunca existe no marketplace hoje.
- **Geração de wrapper** para recursos `user_invokable: true` — decisão pendente, transversal a todo instalador do Worker (`sync`, `get`, `install`): como o Claude Code só expõe slash commands a partir de `.claude/commands/`, o instalador precisará gerar um wrapper nesse diretório para cada skill ou agent invocável pelo usuário.

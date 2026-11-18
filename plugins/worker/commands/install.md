---
# about
name: install
type: command
project: AmFlow
description: Instala um recurso adquirido no Hub em um projeto específico — resolve licença e dependências via MCP e baixa o pacote, confere e instala os arquivos em <projeto>/.claude/
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
uid: ""
source: ""
price: 0

# claude-code
argument-hint: <type>/<name>
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" *)
---

# /amflow-worker:install

Instala um recurso adquirido no Hub em um projeto específico — diferente do [`get`](get.md), que instala em escopo global (`~/.claude/`). Usa a tool `install` do servidor MCP `amflow-worker` (declarado em `.mcp.json`) — sem token no contexto do modelo: o pacote chega por link assinado e quem baixa, confere e grava é o script `fetch_package.py`, não o modelo. Autenticação via OAuth do `/mcp` (M3), cuidada pelo próprio Claude Code na primeira chamada.

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
   | `agent` | `<projeto>/.claude/agents/<name>/` — ou `<projeto>/.claude/agents/<name>.md`, em instalação anterior ao layout de diretório |
   | `hook` | `<projeto>/.claude/hooks/<name>/` |
   | `command` | `<projeto>/.claude/commands/<name>.md` |

   Encontrado → extraia a versão instalada: para `skill`, `metadata.amflow-source` do `SKILL.md`
   (`scripts/frontmatter/skill-frontmatter.md` §3, no repositório AmFlow); para os demais tipos,
   `source:` do arquivo. Use `AskUserQuestion`: **"Manter versão atual"** (encerra) ou **"Verificar
   atualização"** (prossegue). Não encontrado → prossiga direto.

3. Chame a tool `install` do servidor MCP `amflow-worker`:

   ```
   install({ type: "<type>", name: "<name>", scope: "project" })
   ```

   - Erro de licença ("Recurso não encontrado."/"Licença ativa necessária...") → encerre exibindo a mensagem retornada pela tool.
   - Erro de dependência bloqueada ("Dependências bloqueadas — ...") → encerre exibindo a mensagem — já lista quais dependências e por quê (sem licença ou não encontradas no Hub).
   - Sucesso → prossiga com `{name, type, version, expires_at, packages}`. `packages` traz o recurso e as dependências, cada um com `download_url`, `sha256`, `size_bytes` e `file_count`.

4. **Fase 1 — baixar.** Passe o array `packages` ao script, exatamente como a tool o devolveu, sem alterar um caractere dos links:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" baixar --raiz "<projeto>" <<'AMFLOW_PACKAGES_EOF'
   <o array `packages`, em JSON>
   AMFLOW_PACKAGES_EOF
   ```

   O script baixa, confere tamanho e SHA-256, inspeciona os nomes das entradas e **não instala nada**. Guarde a linha `AREA:` da saída. Leia o código de saída:

   | Código | O que fazer |
   |---|---|
   | 0 | Segue |
   | 2 | Erro de uso do script — reporte o `MOTIVO` |
   | 10 | Rede, HTTP diferente de 2xx ou link vencido — chame `install` de novo (link novo) e repita |
   | 11 | Tamanho ou SHA-256 divergente — idem; na **segunda** falha seguida, pare e reporte |
   | 12 | Pacote inválido — pare; é inconsistência do Hub, não do usuário |
   | 13 | Destino — pare e mostre o caminho do `MOTIVO` |
   | 20 | Sem conexão com o domínio do link — diga que esta superfície não suporta o download e não tente de novo |

   Nos códigos 10 a 13 e 20 nenhum recurso instalado foi alterado.

5. **Confirmação humana (M10) — obrigatória, não pule.** Exiba ao usuário as linhas `PACOTE:` (o recurso e as dependências) e `ARQUIVO:` (cada arquivo que será escrito, com o tamanho). Use `AskUserQuestion`: **"Confirmar instalação"** ou **"Cancelar"**. Só prossiga para o passo 6 após confirmação explícita. Cancelar encerra sem instalar nada: descarte a área com `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" descartar --raiz "<projeto>" --area "<AREA>"` — o script recusa caminho que não seja uma área dele e nenhum outro comando apaga arquivo.

6. **Fase 2 — aplicar.** Nenhum recurso é escrito antes deste passo:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" aplicar --raiz "<projeto>" --area "<AREA>"
   ```

   O script confere o SHA-256 de novo, extrai, troca cada recurso por inteiro (a versão anterior só sai depois da nova no lugar), grava `amflow-source` e `amflow-status` na skill, dá permissão de execução a `hook.sh` e apaga a área. Leia o código de saída pela mesma tabela do passo 4; as linhas `INSTALADO:` dizem o que foi instalado.

   `agent`, `hook` e `command` não ganham `amflow-source`/`amflow-status` — fora do escopo desta norma (B-06, `docs/plan/_inbox/_backlog.md`, no repositório AmFlow).

7. Confirme: **"Recurso '`<name>`' instalado em `<projeto>`."** — inclua as dependências instaladas junto, se houver.

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível conectar ao AmFlow. Tente novamente mais tarde."**

## Restrições

- Nunca exiba tokens ao usuário — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.
- Nunca escreva arquivos de recurso com `Write` ou `Edit`: quem escreve é o `fetch_package.py`, que só grava dentro de `<projeto>/.claude/`.
- Nunca rode a fase `aplicar` antes de completar o passo 5 (confirmação).
- Nunca exiba os links de download: carregam um token de curta duração.

## Fora de escopo

- **Tipo `plugin`** — `resources.type` no Hub só aceita `skill|agent|hook|command` (`CHECK` constraint); recurso `plugin` nunca existe no marketplace hoje.
- **Geração de wrapper** para recursos `user_invokable: true` — decisão pendente, transversal a todo instalador do Worker (`sync`, `get`, `install`): como o Claude Code só expõe slash commands a partir de `.claude/commands/`, o instalador precisará gerar um wrapper nesse diretório para cada skill ou agent invocável pelo usuário.

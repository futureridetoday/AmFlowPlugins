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
uid: ""
source: ""
price: 0

# claude-code
argument-hint: <type>/<name>
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" *)
---

# /amflow-worker:get

Instala um recurso específico por nome. Exemplo: `/amflow-worker:get skill/deep-research`. Instala em escopo global (`~/.claude/`), disponível em todos os projetos — distinto do [`install`](install.md), que instala em projeto. Usa a tool `install` do servidor MCP `amflow-worker` com `scope: "global"` (declarado em `.mcp.json`) — sem token no contexto do modelo: o pacote chega por link assinado e quem baixa, confere e grava é o script `fetch_package.py`, não o modelo.

Argumento recebido: `$ARGUMENTS` — formato esperado `<type>/<name>` com `type` ∈ `skill | agent | command | hook`. Se ausente ou fora do formato, pergunte ao usuário qual recurso instalar.

## Processo

1. Chame a tool `install` do servidor MCP `amflow-worker`:

   ```
   install({ type: "<type>", name: "<name>", scope: "global" })
   ```

   - Erro de licença → encerre exibindo a mensagem retornada pela tool.
   - Erro de dependência bloqueada → encerre exibindo a mensagem retornada.
   - Sucesso → prossiga com `{name, type, version, expires_at, packages}`.

2. **Fase 1 — baixar.** A raiz é o diretório home — a pasta que **contém** `.claude/` —, e o script mantém o prefixo `.claude/` do caminho de cada arquivo. Passe o array `packages` ao script, exatamente como a tool o devolveu, sem alterar um caractere dos links:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" baixar --raiz "$HOME" <<'AMFLOW_PACKAGES_EOF'
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

3. **Confirmação humana (M10) — obrigatória, não pule.** Exiba as linhas `PACOTE:` (o recurso e as dependências) e `ARQUIVO:` (cada arquivo que será escrito, com o tamanho). Use `AskUserQuestion`: **"Confirmar instalação"** ou **"Cancelar"**. Só prossiga para o passo 4 após confirmação explícita. Cancelar encerra sem instalar nada: descarte a área com `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" descartar --raiz "$HOME" --area "<AREA>"` — o script recusa caminho que não seja uma área dele e nenhum outro comando apaga arquivo.

4. **Fase 2 — aplicar.** Nenhum recurso é escrito antes deste passo:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" aplicar --raiz "$HOME" --area "<AREA>"
   ```

   O script confere o SHA-256 de novo, extrai, troca cada recurso por inteiro, grava o registro local na skill, dá permissão de execução a `hook.sh` e apaga a área. Leia o código de saída pela mesma tabela do passo 2.

5. Confirme: **"Recurso '`<name>`' instalado."** — inclua as dependências instaladas junto, se houver.

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível conectar ao AmFlow. Tente novamente mais tarde."**

## Restrições

- Nunca exiba tokens ao usuário.
- Nunca escreva arquivos de recurso com `Write` ou `Edit`: quem escreve é o `fetch_package.py`, que só grava dentro de `~/.claude/`.
- Nunca rode a fase `aplicar` antes de completar o passo 3 (confirmação).
- Nunca exiba os links de download: carregam um token de curta duração.

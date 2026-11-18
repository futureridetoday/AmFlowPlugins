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
uid: ""
source: ""
price: 0

# claude-code
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" *)
---

# /amflow-worker:hub-update

Aplica atualizações nos recursos instalados em `~/.claude/`, após confirmação do usuário. Atua apenas sobre `update_available` — recursos `unlicensed` são exibidos com aviso, mas nunca atualizados nem removidos. Usa as tools `check_updates` e `update` do servidor MCP `amflow-worker`; o pacote chega por link assinado e quem baixa, confere e grava é o script `fetch_package.py`, não o modelo.

## Processo

1. Verifique as atualizações — mesma coleta e consulta do [`/amflow-worker:hub-check`](hub-check.md):

   - Colete `name`, `type`, `version` do frontmatter dos recursos instalados em `~/.claude/` (`skills/*/SKILL.md`, `agents/*.md`, `commands/*.md`, `hooks/*/*.md`).
   - Chame a tool `check_updates({ installed: [...] })` (máximo de 200 itens por lote).

2. Separe os resultados:
   - Sem itens `update_available` → encerre com **"Nenhuma atualização disponível."**
   - Itens `unlicensed` → exiba **"`<name>`: licença expirada ou revogada — `<hub_url>`"** e ignore-os na atualização.

3. Para cada recurso com `update_available`, chame a tool `update`:

   ```
   update({ type: "<type>", name: "<name>", scope: "global" })
   ```

   Resposta: `{name, type, version, expires_at, packages}`. Erro da tool → registre e continue os demais. Status da telemetria nesse caso: `partial`.

4. **Fase 1 — baixar, um recurso por vez.** A raiz é o diretório home — a pasta que **contém** `.claude/`. Passe o array `packages` do recurso ao script, exatamente como a tool o devolveu, sem alterar um caractere dos links:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" baixar --raiz "$HOME" <<'AMFLOW_PACKAGES_EOF'
   <o array `packages`, em JSON>
   AMFLOW_PACKAGES_EOF
   ```

   O script **não altera nada instalado**. Guarde a linha `AREA:` de cada recurso baixado. Leia o código de saída:

   | Código | O que fazer |
   |---|---|
   | 0 | Segue |
   | 2 | Erro de uso do script — reporte o `MOTIVO` |
   | 10 | Rede, HTTP diferente de 2xx ou link vencido — chame `update` de novo (link novo) e repita |
   | 11 | Tamanho ou SHA-256 divergente — idem; na **segunda** falha seguida, pare e reporte |
   | 12 | Pacote inválido — pare; é inconsistência do Hub, não do usuário |
   | 13 | Destino — pare e mostre o caminho do `MOTIVO` |
   | 20 | Sem conexão com o domínio do link — diga que esta superfície não suporta o download e não tente de novo |

   Nos códigos 10 a 13 e 20 nenhum recurso instalado foi alterado.

   Falha num recurso → registre e continue os demais (status `partial`); código 20 encerra o lote.

5. **Confirmação humana (M10) — obrigatória, não pule.** Exiba a lista de recursos a atualizar (nome, versão instalada → versão nova, changelog) e as linhas `PACOTE:` e `ARQUIVO:` de cada um. Use `AskUserQuestion`: **"Aplicar atualizações"** ou **"Cancelar"**. Só prossiga para o passo 6 após confirmação explícita. Cancelar encerra sem alterar nada: descarte cada área com `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" descartar --raiz "$HOME" --area "<AREA>"` — o script recusa caminho que não seja uma área dele e nenhum outro comando apaga arquivo.

6. **Fase 2 — aplicar, uma área por vez.** A versão anterior só sai depois da nova no lugar:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" aplicar --raiz "$HOME" --area "<AREA>"
   ```

   Falha num recurso → registre, continue os demais e reporte ao final (status `partial`).

7. Exiba o resumo: **"X recursos atualizados."** (acrescente os que falharam, se houver).

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Não foi possível verificar atualizações. Tente novamente mais tarde."**

## Restrições

- Nunca exiba tokens ao usuário.
- Nunca rode a fase `aplicar` sem a confirmação do passo 5.
- Nunca escreva arquivos de recurso com `Write` ou `Edit`: quem escreve é o `fetch_package.py`, que só grava dentro de `~/.claude/`.
- Nunca exiba os links de download: carregam um token de curta duração.

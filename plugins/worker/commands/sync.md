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
uid: ""
source: ""
price: 0

# claude-code
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" *)
---

# /amflow-worker:sync

Sincroniza todos os recursos com licença ativa — públicos adquiridos e exclusivos atribuídos. Instala em escopo global (`~/.claude/`), disponível em todos os projetos. Recursos instalados por outras fontes (git, cópia manual) não são tocados. Usa as tools `list_active_licenses` e `install` do servidor MCP `amflow-worker`; o pacote chega por link assinado e quem baixa, confere e grava é o script `fetch_package.py`, não o modelo.

## Processo

1. Chame a tool `list_active_licenses` (sem argumentos). Resposta: `{ items: [{ name, type, version, visibility }] }`.

   Array vazio → informe **"Nenhum recurso licenciado para sincronizar."** e vá ao passo 6.

2. Para cada recurso da lista, chame a tool `install`:

   ```
   install({ type: "<type>", name: "<name>", scope: "global" })
   ```

   Resposta: `{name, type, version, expires_at, packages}`. Erro da tool (licença, dependência bloqueada, limite de chamadas) → registre a falha do recurso e continue os demais. Status da telemetria nesse caso: `partial`.

3. **Fase 1 — baixar, um recurso por vez.** A raiz é o diretório home — a pasta que **contém** `.claude/`. Passe o array `packages` do recurso ao script, exatamente como a tool o devolveu, sem alterar um caractere dos links:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" baixar --raiz "$HOME" <<'AMFLOW_PACKAGES_EOF'
   <o array `packages`, em JSON>
   AMFLOW_PACKAGES_EOF
   ```

   O script **não instala nada**. Guarde a linha `AREA:` de cada recurso baixado. Leia o código de saída:

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

   Falha num recurso → registre e continue os demais (status `partial`); código 20 encerra o lote.

4. **Confirmação humana (M10) — obrigatória, não pule.** Com todos os recursos baixados, exiba o lote: as linhas `PACOTE:` e `ARQUIVO:` de cada um. Use `AskUserQuestion`: **"Sincronizar N recursos"** ou **"Cancelar"**. Só prossiga para o passo 5 após confirmação explícita — uma confirmação cobre o lote inteiro (não pergunte recurso por recurso). Cancelar encerra sem instalar nada: descarte cada área com `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" descartar --raiz "$HOME" --area "<AREA>"` — o script recusa caminho que não seja uma área dele e nenhum outro comando apaga arquivo.

5. **Fase 2 — aplicar, uma área por vez:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_package.py" aplicar --raiz "$HOME" --area "<AREA>"
   ```

   Falha num recurso → registre e continue os demais (status `partial`).

6. Exiba o resumo: **"X recursos sincronizados."** (acrescente os que falharam, se houver).

## Tratamento de erros

- Falha ao chamar a tool (Hub/MCP indisponível) → **"Hub indisponível. Os recursos instalados localmente continuam funcionando."**

## Restrições

- Nunca exiba tokens ao usuário.
- Nunca escreva arquivos de recurso com `Write` ou `Edit`: quem escreve é o `fetch_package.py`, que só grava dentro de `~/.claude/`.
- Nunca rode a fase `aplicar` antes de completar o passo 4 (confirmação do lote).
- Nunca exiba os links de download: carregam um token de curta duração.

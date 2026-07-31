---
# about
name: publish-status
type: command
project: AmFlow
description: Consulta o Hub via MCP e exibe o status de submissão dos recursos publicados no projeto; sincroniza o campo status local
tags: [publish, status, submission, creator, mcp]

# history
author: Bortoli
created: 2026-06-14
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
argument-hint: [--resource <nome>]
---

# /amflow-builder:publish-status

Consulta o Hub e exibe o status atual de submissão dos recursos publicados no projeto. Sincroniza o campo `status` no arquivo local quando detecta mudança. Usa a tool `submission_status` do servidor MCP `amflow`.

Argumento opcional: `--resource <nome>` — filtra para um único recurso.

## Processo

### Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow`.

- Sucesso → sessão válida; prossiga. Com sessão já ativa, o `me` responde direto sem novo login.
- Sem sessão / erro → o conector `amflow` não está autorizado nesta sessão. **Encerre aqui** — não consulte o Hub. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

### Fase 1 — Coletar recursos publicados

1. Verificar `.claude/CLAUDE.md` no diretório atual — encerrar com erro se ausente.

2. Escanear o projeto em busca de recursos com `source: hub/...` no frontmatter:
   - `skill` → `SKILL.md` em `.claude/skills/*/`
   - `agent` → `.claude/agents/*.md` (excluir `*-workflow.md`)
   - `hook` → `.claude/hooks/*/hook.json`
   - `command` → `.claude/commands/*.md`

   Extrair de cada arquivo: `name`, `type`, `version`, `hub_id`, `status`.

   Se `--resource <nome>` informado → filtrar apenas esse recurso. Se não tiver `source: hub/...` → encerrar: **"<nome> ainda não foi publicado. Use /amflow-builder:publish para publicar."**

   Se nenhum recurso encontrado → encerrar: **"Nenhum recurso publicado encontrado no projeto. Use /amflow-builder:publish para publicar um recurso."**

### Fase 2 — Consultar Hub

3. Para cada recurso, chame a tool `submission_status({ hub_id: "<hub_id>" })`:

   Resposta: `{ hub_id, name, type, version, submission_id, status, feedback, updated_at }`.

   Erro da tool (recurso não encontrado, sem submissão) → registrar aviso por recurso e continuar os demais.

### Fase 3 — Exibir tabela

4. Exibir tabela de status com colunas: recurso | tipo | versão | status | atualizado.

5. Quando `status` for `rejected` ou `changes_requested`, exibir o feedback abaixo da tabela:

   ```
   ─────────────────────────────────────────────────────────────────────────
   Feedback — <nome> (<status>):
     "<feedback do Manager>"
   ```

### Fase 4 — Sincronizar status local

6. Para cada recurso em que o status Hub difere do arquivo local, atualizar com a ferramenta Edit:

   | Status Hub | Status local |
   |---|---|
   | `approved` | `stable` |
   | `rejected` | `draft` |
   | `changes_requested` | `draft` |
   | `pending_review` | `published` (sem alteração) |

   Arquivo a atualizar por tipo:
   - `skill` → `SKILL.md` (campo `status` no frontmatter)
   - `agent` → `agent.md` (campo `status` no frontmatter)
   - `hook` → `hook.json` (campo `status` na raiz)
   - `command` → `command.md` (campo `status` no frontmatter)

7. Exibir o sync realizado:

   ```
   Status local sincronizado:
     <nome>  published → draft  (changes_requested)
   ```

### Fase 5 — Próximos passos

8. Sugerir ação por status:

   | Status | Mensagem |
   |---|---|
   | `approved` | `<nome> está live no marketplace.` |
   | `rejected` | `<nome> foi recusado. Corrija o recurso e execute /amflow-builder:publish.` |
   | `changes_requested` | `<nome> requer ajustes. Leia o feedback acima e execute /amflow-builder:publish.` |
   | `pending_review` | `<nome> está aguardando revisão.` |

## Restrições

- Nunca exibir tokens ao usuário.
- Usar a ferramenta Edit para alterar `status` — nunca sobrescrever o arquivo inteiro.
- Sincronizar apenas o campo `status` — nunca alterar outros campos sem solicitação.

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
version: 2.1.0
updated: 2026-08-27

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

Consulta o Hub e exibe o status atual de submissão dos recursos publicados no projeto. Sincroniza o campo `status` no arquivo local quando detecta mudança. Usa a tool `submission_status` do servidor MCP `amflow-builder`.

Argumento opcional: `--resource <nome>` — filtra para um único recurso.

## Processo

### Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → sessão válida; prossiga. Com sessão já ativa, o `me` responde direto sem novo login.
- Sem sessão / erro → o conector `amflow-builder` não está autorizado nesta sessão. **Encerre aqui** — não consulte o Hub. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

### Fase 1 — Coletar recursos publicados

1. Verificar `.claude/CLAUDE.md` no diretório atual — encerrar com erro se ausente.

2. Escanear o projeto em busca de recursos **com identificador do Hub preenchido**:
   - `skill` → `SKILL.md` em `.claude/skills/*/`
   - `agent` → `.claude/agents/*.md` (excluir `*-workflow.md`)
   - `hook` → `.claude/hooks/*/hook.json`
   - `command` → `.claude/commands/*.md`

   **Onde cada dado mora, por tipo.** `skill` segue norma própria — o porquê está em
   `builder-resource-standards`: o dado do AmFlow vive no bloco `metadata`, com prefixo `amflow-`.
   Os outros três seguem a tabela do `.claude/CLAUDE.md`, com os campos no topo.

   | Dado | `skill` | `agent`, `hook`, `command` |
   |---|---|---|
   | versão | `metadata.amflow-version` | `version` |
   | estado | `metadata.amflow-status` | `status` |
   | identificador no Hub | `metadata.amflow-hub-id` | `hub_id` |

   `name` está no topo nos quatro tipos; `type` vem da pasta em que o arquivo foi encontrado, não do
   frontmatter.

   **O critério de descoberta é o identificador do Hub, não a origem.** A norma reserva
   `amflow-source` à cópia instalada — a fonte no repositório do Creator nunca a tem, e procurar por
   `source: hub/...` não encontraria skill nenhuma. Nos outros três tipos, `source` continua presente
   e serve de sinal de apoio, mas quem decide é o identificador.

   Se `--resource <nome>` informado → filtrar apenas esse recurso. Sem identificador do Hub →
   encerrar: **"<nome> ainda não foi publicado. Use /amflow-builder:publish para publicar."**

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

6. Para cada recurso em que o status Hub difere do arquivo local, atualizar com a ferramenta Edit.
   **O mapeamento difere por tipo, porque os domínios de estado são diferentes.**

   `skill` — o domínio da norma tem os quatro estados do Hub, e o mapeamento é direto:

   | Status Hub | `metadata.amflow-status` |
   |---|---|
   | `approved` | `published` |
   | `pending_review` | `pending_review` |
   | `changes_requested` | `changes_requested` |
   | `rejected` | `rejected` |

   `agent`, `hook` e `command` — domínio do `.claude/CLAUDE.md`, sem `pending_review` nem
   `changes_requested`, então a recusa e o pedido de ajuste colapsam em `draft`:

   | Status Hub | `status` |
   |---|---|
   | `approved` | `stable` |
   | `rejected` | `draft` |
   | `changes_requested` | `draft` |
   | `pending_review` | `published` (sem alteração) |

   Arquivo a atualizar por tipo:
   - `skill` → `SKILL.md` (`amflow-status`, dentro de `metadata`)
   - `agent` → `<nome>.md` (campo `status` no frontmatter)
   - `hook` → `hook.json` (campo `status` na raiz)
   - `command` → `command.md` (campo `status` no frontmatter)

   **Este comando é o único que move uma skill para `published`.** O `/amflow-builder:publish` grava
   `pending_review` ao submeter; sem esta sincronização, o estado de toda skill publicada trava ali.
   É por isso que o mapeamento de `skill` preserva os quatro estados em vez de colapsá-los: a norma
   atribui `changes_requested`, `rejected`, `published` e `suspended` a este comando, e colapsar em
   `draft` apagaria a razão da recusa do próprio arquivo.

7. Exibir o sync realizado:

   ```
   Status local sincronizado:
     minha-skill    pending_review → changes_requested  (changes_requested)
     meu-command    published      → draft              (changes_requested)
   ```

   O mesmo status do Hub produz estados locais diferentes: a skill guarda a razão, o command a
   colapsa em `draft`. É consequência dos dois domínios, não inconsistência.

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

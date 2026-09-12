# Guia de Referência — Criação de Subagentes (Claude Code)

Extraído da documentação oficial do Claude Code:
[Create custom subagents](https://docs.claude.com/en/docs/claude-code/sub-agents).
Consulte a fonte antes de decidir algo que diverja deste resumo — ela pode ter mudado desde a extração.

Este documento acompanha [`agent.md`](./agent.md) (template) e [`agent-description.md`](./agent-description.md)
como material de apoio — não é o template em si.

---

## Princípios

- **Isolamento de contexto** — o subagente explora/busca no próprio contexto; só o resumo volta para a conversa principal.
- **Reuso** — configuração compartilhável entre projetos (`.claude/agents/` versionado) ou entre sessões pessoais (`~/.claude/agents/`).
- **Restrição de superfície** — `tools`/`disallowedTools` limitam o raio de ação (ex.: um revisor só com `Read, Grep, Glob`).
- **Especialização** — system prompt próprio, no corpo do arquivo.
- **Controle de custo** — roteamento de modelo por subagente (`model: haiku` para tarefas baratas).

## Estrutura do arquivo

Markdown com frontmatter YAML + corpo = system prompt:

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer...
```

## Campos do frontmatter

| Campo | Obrigatório | Função |
|---|---|---|
| `name` | Sim | minúsculas-com-hífen, sem `:` (reservado a plugin-scoped identifiers) |
| `description` | Sim | trigger de delegação — o que dispara a invocação |
| `tools` | Não | allowlist; omitido = herda tudo |
| `disallowedTools` | Não | denylist sobre o herdado/especificado |
| `model` | Não | `sonnet`\|`opus`\|`haiku`\|`fable`\|ID completo\|`inherit` |
| `permissionMode` | Não | `default`\|`acceptEdits`\|`auto`\|`dontAsk`\|`bypassPermissions`\|`plan`\|`manual` |
| `maxTurns` | Não | teto de turnos; saída marcada como parcial ao atingir |
| `skills` | Não | pré-carrega conteúdo completo da skill no startup |
| `mcpServers` | Não | referência a servidor existente ou definição inline |
| `hooks` | Não | `PreToolUse`/`PostToolUse`/`Stop` escopados ao subagente |
| `memory` | Não | `user`\|`project`\|`local` |
| `background` | Não | `true` força background mesmo se a sessão pede foreground |
| `effort` | Não | `low`\|`medium`\|`high`\|`xhigh`\|`max` |
| `isolation` | Não | `worktree` — git worktree temporário |
| `color` | Não | cor de exibição |
| `initialPrompt` | Não | auto-submetido como primeiro turno quando roda como sessão principal |
| `experimental.cacheTtl` | Não | `5m`\|`1h` |

## Localização e escopo — prioridade

| Local | Escopo | Prioridade |
|---|---|---|
| Managed settings | organização | 1 (mais alta) |
| `--agents` (CLI) | sessão atual | 2 |
| `.claude/agents/` | projeto | 3 |
| `~/.claude/agents/` | todos os projetos do usuário | 4 |
| `agents/` do plugin | onde o plugin está habilitado | 5 (mais baixa) |

Nome duplicado entre locais → vence o de maior prioridade. Subpastas (`agents/review/`) são só
organização — não afetam o identificador.

## Ferramentas

- **Sempre removidas de todo subagente**: `Agent`, `AskUserQuestion`, `EndConversation`,
  `EnterPlanMode`, `ExitPlanMode` (exceto `permissionMode: plan`), `ScheduleWakeup`, `TaskOutput`,
  `WaitForMcpServers`, `Workflow`.
- **Removidas só em background**: tudo exceto `Read, Grep, Glob, Bash, PowerShell, Edit, Write,
  NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree,
  Monitor, TaskStop, SendMessage, Artifact`.
- **Padrões MCP**: `mcp__<server>` (servidor inteiro), `mcp__<server>__*` (ferramentas específicas),
  `mcp__*` (só em `disallowedTools`, remove todo MCP).
- **Restringir quais subagentes um orquestrador pode invocar**:
  `tools: Agent(worker, researcher), Read, Bash` — omitir `Agent` bloqueia spawning por completo.

## Modos de permissão

`default` (pergunta) · `acceptEdits` (auto-aceita edição/comandos comuns) · `auto` (classificador
revisa em background) · `dontAsk` (nega prompts automaticamente) · `bypassPermissions` (pula, só se
a sessão principal também usa) · `plan` (só leitura).

Regra de herança: se a sessão principal está em `bypassPermissions`/`acceptEdits`/`auto`, o
subagente herda esse modo e ignora `permissionMode` próprio.

## Boas práticas para `description`

- Breve (~100–150 caracteres); soma de todas as descriptions carregadas não deve passar 15.000 tokens.
- Usar "**use proactively**" quando o subagente deve ser invocado sem pedido explícito.
- Nomear a situação de gatilho, não só a função — "Use after writing or modifying code" em vez de
  descrição genérica.

## Regras de nomenclatura / o que é ignorado silenciosamente

Erro só aparece no debug log — não há aviso na tela:

- Sem `name` no frontmatter → tratado como documentação, não como agente.
- Primeira linha não é `---` → ignorado.
- `name` começando com `-` ou contendo `:` → erro.
- `name` presente mas sem `description` → erro.
- YAML inválido → erro.

## Resolução de modelo (ordem)

1. Parâmetro passado no spawn.
2. `model` do frontmatter (`inherit` = modelo da conversa principal).
3. `CLAUDE_CODE_SUBAGENT_MODEL`.
4. Modelo da conversa principal.

## Contexto na inicialização — o que entra e o que não entra

**Entra**: system prompt customizado, task message, `CLAUDE.md`, snapshot de `git status`, skills
pré-carregadas, roster de agentes-irmãos nomeados na sessão.

**Não entra**: histórico da conversa principal, output style, auto-memory da sessão principal.

## Variáveis de ambiente relevantes

`CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`,
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`
(default 20), `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`.

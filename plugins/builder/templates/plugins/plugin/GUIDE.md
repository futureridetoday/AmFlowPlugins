---
# about
name: plugin-guide
type: doc
project: AmFlow
description: Guia de preenchimento do plugin.json e da estrutura de diretórios de um plugin Claude Code — campos do manifesto, componentes opcionais, portabilidade e checklist de validação
tags: [builder, plugin, template, guide]

# history
author: Bortoli
created: 2026-09-22
status: stable
version: 1.0.0
updated: 2026-09-22

# system
scope: project
auto_load: false
dependencies: []

# referências de criação
# [1] Claude Code — Plugins reference   https://code.claude.com/docs/en/plugins-reference
---

# Guia de Preenchimento do Plugin

Este template produz um **plugin Claude Code real** — instalável via marketplace, caminho local
ou `skills-dir` — não um recurso solto que vive dentro de `.claude/` de um único projeto. Use-o
quando o objetivo declarado for empacotar e distribuir, não só construir.

---

## Anatomia obrigatória

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # único arquivo que pode ficar aqui dentro
├── plugin-description.md    # ao lado do .claude-plugin/, não dentro
├── commands/                 # opcional — só se o plugin expõe slash commands
├── agents/                   # opcional — só se o plugin expõe subagents
├── skills/<nome>/SKILL.md    # opcional — só se o plugin expõe skills
├── hooks/hooks.json          # opcional — só se o plugin reage a eventos
├── .mcp.json                 # opcional — só se o plugin bundla servidor MCP
└── scripts/                  # opcional — scripts que hooks/commands chamam
```

**Regra dura, sem exceção:** `.claude-plugin/` guarda só o `plugin.json`. Todo componente —
`commands/`, `agents/`, `skills/`, `hooks/`, `.mcp.json` — fica na **raiz do plugin**, nunca
dentro de `.claude-plugin/`. É o erro mais comum e o Claude Code não avisa: o componente
simplesmente não é descoberto.

**Só crie a pasta do componente que o plugin de fato usa.** Pasta vazia ou com `.gitkeep` como
único conteúdo já foi defeito medido nos plugins deste repositório (Worker/Builder, unidade
`0003-01` do plano `0003-public-catalog`) — shipped como conteúdo do plugin, sem função.

---

## O manifesto (`plugin.json`)

Este template nasce com os cinco campos que os dois plugins reais deste repositório
(`plugins/worker/.claude-plugin/plugin.json`, `plugins/builder/.claude-plugin/plugin.json`) usam
de fato:

| Campo | Obrigatório | Forma |
|---|---|---|
| `name` | **Sim — único campo que a spec exige** | kebab-case, sem espaço, único entre plugins instalados |
| `displayName` | Não | Texto livre, o que aparece no picker `/plugin`. Sem ele, usuário vê `name` |
| `description` | Não | Frase curta do propósito |
| `version` | Não | Semver. Sem ela, a versão vem da fonte (tag git, entrada do marketplace) |
| `author` | Não | Objeto — `{"name": "...", "email": "...", "url": "..."}`. Nunca string solta |

Campos adicionais existem e são reconhecidos, mas este template não os inclui por padrão —
adicione só quando o plugin precisar:

| Campo | Para quê |
|---|---|
| `homepage`, `repository`, `license`, `keywords` | Metadados de descoberta — só valem quando o plugin tem essas informações de verdade |
| `metadata` | Objeto livre — **o Claude Code nunca lê**, nunca afeta comportamento. É onde entraria rastreio específico do AmFlow (`hub_id`, status de publicação) *se* `plugin` vier a ser tipo distribuído pelo Hub — decisão em aberto, não implementada aqui. Mesmo padrão que `module.json` já usa em `metadata.amflow-status` |
| `defaultEnabled` | `false` se o plugin deve nascer desabilitado. Padrão é `true` |
| `dependencies` | Outros plugins que este exige, com restrição de versão opcional |
| `userConfig` | Valores que o Claude Code pergunta ao usuário quando o plugin é habilitado — a forma oficial de coletar config (tipo, título, descrição, `sensitive` para segredo) |
| `skills` / `commands` / `agents` / `hooks` / `mcpServers` / `outputStyles` / `lspServers` | *Path override* — string ou array apontando para um caminho **diferente** do padrão. Não é lista de componentes: declarar `"agents": ["a", "b"]` esperando dois agents chamados `a` e `b` é o erro mais fácil de cometer aqui. O padrão já é descoberto sozinho — só declare quando o layout for não-padrão |

Campo não reconhecido nunca quebra o carregamento — o Claude Code ignora e `claude plugin
validate` avisa, não erra. Isso não é licença para lixo: é rede de segurança, não convite.

---

## Componentes opcionais

### `commands/`

Um `.md` por slash command, frontmatter com `description` (e `allowed-tools` quando o comando
usa tool que precisa de pré-aprovação, inclusive tool MCP: `mcp__plugin_<nome>_<servidor>__*`).

### `agents/`

Um `.md` por subagent, frontmatter com `description`. Subpasta agrega ao nome do agent
(`agents/review/accessibility.md` carrega como `<plugin>:review:accessibility`).

### `skills/<nome>/`

Uma pasta por skill, com `SKILL.md` dentro — mesma regra de frontmatter da norma de skill do
AmFlow (`scripts/frontmatter/skill-frontmatter.md`, no AmFlow), o restante da pasta é o corpo da
skill (scripts/, references/, assets/).

### `hooks/hooks.json`

**Formato wrapper — diferente do `.claude/settings.json` do usuário.** É o erro mais fácil de
cometer em silêncio, porque os dois formatos são JSON válido e só um funciona aqui:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format.sh" }
        ]
      }
    ]
  }
}
```

Sem o `"hooks"` externo envolvendo os eventos, o arquivo é sintaticamente válido e não faz nada.

### `.mcp.json`

Um servidor por chave. `stdio` para processo local, `sse`/`http`/`ws` para serviço hospedado —
ver exemplos e autenticação na doc oficial (link no topo deste arquivo). Nomeie tools MCP em
`allowed-tools` de forma explícita, nunca com wildcard (`mcp__plugin_x_y__*`) em produção.

---

## Portabilidade — nunca hardcode caminho

| Variável | Resolve para | Onde usar |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | Diretório onde o plugin foi instalado | Scripts, binários e configs que o próprio plugin traz |
| `${CLAUDE_PLUGIN_DATA}` | Diretório persistente, sobrevive a atualização do plugin | `node_modules`, venv, cache, código gerado |
| `${CLAUDE_PROJECT_DIR}` | Raiz do projeto onde o plugin está rodando | Scripts e config locais do projeto do usuário, não do plugin |

Essas três variáveis existem no ambiente de hooks e de subprocessos MCP/LSP — **não** existem no
ambiente de um comando que o Claude executa via tool Bash. Em conteúdo de skill/agent/comando, é
o Claude Code que substitui o placeholder ao carregar o conteúdo — escreva o texto literal
`${CLAUDE_PLUGIN_ROOT}`, nunca um caminho absoluto calculado à mão.

---

## Padrões comuns

- **Plugin mínimo** — um `commands/` com um único comando, `plugin.json` só com `name`.
- **Plugin focado em skill** — só `skills/`, nada mais.
- **Plugin completo** — combina vários componentes; é a forma do Worker e do Builder deste
  repositório.

Comece pelo menor que resolve o problema — cada pasta a mais é superfície a manter.

---

## Antes de considerar pronto

1. `claude plugin validate <caminho-do-plugin>` sem erro. `--strict` trata aviso como erro — rode
   com essa flag antes de publicar, não só o modo tolerante.
2. Nenhum caminho absoluto ou `~/` em hook, MCP ou script — só `${CLAUDE_PLUGIN_ROOT}` e as duas
   variáveis irmãs.
3. `hooks/hooks.json`, se existir, tem o `"hooks"` externo envolvendo os eventos.
4. Nenhuma pasta de componente vazia ou só com `.gitkeep`.
5. `version` do `plugin.json` bate com a primeira linha de `plugin-description.md`.
6. `name` não muda entre versões — é o identificador que quem já instalou carrega.

Terminar o desenvolvimento do recurso deveria significar isto: rodar o checklist acima e subir o
`version`. Se abrir esta lista revelar que falta mover arquivo de lugar ou reescrever o manifesto,
o recurso não nasceu dentro da estrutura de plugin — nasceu fora e está sendo empacotado agora,
que é exatamente o retrabalho que este template existe para evitar.

---

## Exemplos reais neste repositório

`plugins/worker/.claude-plugin/plugin.json` e `plugins/builder/.claude-plugin/plugin.json` — os
dois manifestos que este template usa como forma mínima de referência. Ambos rodando, ambos
auditados contra o padrão oficial em 2026-07 (`auditoria-plugins-distribuicao.md`, §3, no AmFlow).

---

## Em aberto

Este template não assume integração com o pipeline de publicação do AmFlow — `hub_id`, status de
revisão, preço. Ainda não está decidido se `plugin` será um tipo de recurso distribuído pelo Hub.
Se isso for decidido, o rastreio entra em `metadata` (ver tabela acima), sem mexer nos campos
reais do manifesto.

---
# about
name: new-project
type: command
project: AmFlow
description: Inicializa a estrutura .claude/ e cria os arquivos base de um novo projeto via survey guiado
tags: [new, onboarding, new-project, creator]

# history
author: Bortoli
created: 2026-06-14
status: stable
version: 1.0.0
updated: "2026-07-15"

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-builder:new-project

Inicializa a estrutura `.claude/` e cria os arquivos base de um novo projeto AmFlow. Disponível para Creators e Managers com o plugin Builder instalado. Renomeado de `amflow-start` (D11) e, nesta versão, de `/amflow-builder:new`.

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação (inclusive o survey e qualquer criação de arquivo), chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → o comando segue. Com sessão já ativa, o `me` responde direto e o comando segue sem novo login. Nenhum arquivo gerado carrega o `user_id`: a Fase 0 é o gate de autenticação do plugin, não fonte de carimbo.
- Sem sessão / erro → o conector `amflow` não está autorizado nesta sessão. **Encerre aqui** — não prossiga para o survey nem crie qualquer arquivo. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

## Survey (Passos 1–4)

Faça uma pergunta por vez, usando o contexto acumulado para gerar sugestões.

### Passo 1 — Pasta do projeto

Executar `pwd` e exibir o caminho atual como sugestão primária. Aceitar "Informar outro caminho" para texto livre.

### Passo 2 — Nome do projeto

Derivar o nome do último segmento do caminho (ex: `/Users/rafael/Code/MeuApp` → `MeuApp`). Exibir como sugestão; aceitar "Informar outro nome".

### Passo 3 — Tipo de projeto

| Opção | Descrição |
|---|---|
| Design | identidade visual, UX/UI e design de produto |
| Development | aplicações, APIs, plataformas e sistemas |
| Marketing | estratégia, campanhas e produção de conteúdo |
| AI Builder | automações, agentes e recursos de IA |

### Passo 4 — Descrição do projeto

Faça de 1 a 3 perguntas objetivas, uma por vez, para entender o projeto — o que ele faz, para quem, e qual o objetivo principal. Use as respostas acumuladas (incluindo nome e tipo) para propor uma descrição de uma frase.

Exibir a descrição proposta como sugestão primária e aceitar "Outro (digitar)" para texto livre. A resposta final é gravada em `<descricao>`.

## Execução (Passo 5)

### 5.0 — Pré-execução

```bash
test -d "<pasta>"
```
Não existe → encerrar: **"Diretório não encontrado: <pasta>"**

```bash
test -f "<pasta>/.claude/CLAUDE.md"
```
Existe → encerrar: **"Projeto já configurado em <pasta> — execute /amflow-builder:build para criar recursos."**

```bash
DATA=$(date +%Y-%m-%d)
AUTHOR=$(git -C "<pasta>" config user.name 2>/dev/null || git config --global user.name 2>/dev/null)
```
`DATA` e `AUTHOR` não têm destino nos arquivos gerados desde que o `CLAUDE.md` deixou de ter frontmatter. `AUTHOR` vazio não bloqueia a execução.

### 5.1 — Criar estrutura

```bash
mkdir -p "<pasta>/.claude/skills"
mkdir -p "<pasta>/.claude/agents"
mkdir -p "<pasta>/.claude/hooks"
mkdir -p "<pasta>/.claude/commands"
mkdir -p "<pasta>/.claude/plugins"
mkdir -p "<pasta>/.claude/modules"
mkdir -p "<pasta>/.claude/rules"
```

### 5.2 — Gerar `.claude/CLAUDE.md`

Gerar com a ferramenta Write. O arquivo é composto por: seções fixas → seções por tipo → fragmentos padrão.

**Sem frontmatter.** O `CLAUDE.md` não é manifesto de recurso: o Claude Code o entrega como mensagem de usuário e não interpreta bloco YAML no topo — frontmatter ali é texto que consome contexto em toda sessão sem ser lido por nada. O arquivo começa direto no `#` do título.

#### Seções fixas (todos os tipos)

```markdown
# <nome> — Instruções do Projeto

## Identidade

| Campo | Valor |
|---|---|
| Tipo de projeto | <tipo> |

## Visão Geral

<descricao>

## Recursos AmFlow

Recurso novo — skill, agent, command, hook, plugin, workflow ou module — se cria por
`/amflow-builder:build`, que aplica o template e o frontmatter da norma vigente. É o
que torna o recurso publicável: o Hub recusa submissão com `metadata` incompleto.

Pedido de criação que chegue sem o comando → sugerir o comando antes de escrever
qualquer arquivo.

### Onde cada recurso vive

| Tipo | Caminho |
|---|---|
| skill | `.claude/skills/<nome>/` |
| agent | `.claude/agents/<nome>/` |
| hook | `.claude/hooks/<nome>/` |
| command | `.claude/commands/<nome>.md` |
| module | `.claude/modules/<nome>/` |
| plugin | `.claude/plugins/<nome>.json` |
| workflow | `.claude/agents/<nome>-workflow.md` |

Regra de projeto vai em `.claude/rules/`, um arquivo por assunto. Regra com `paths` no
topo só carrega quando o Claude toca arquivo que casa com o glob.
```

#### Seções por tipo

Incluir **apenas** o bloco correspondente ao tipo escolhido:

**Design:**
```markdown
## Recursos Instalados

## Restrições

**Assets**
- Nunca usar assets fora de `design/` como fonte
- Tokens de design alterados na fonte antes de propagar para implementação

**Git**
- PRs para `main` exigem revisão manual
- Nunca fazer force push em `main`

**Autonomia do Claude**
- Decisões de direção criativa exigem aprovação prévia
- Ações que afetam mais de 5 arquivos exigem apresentação de plano antes de executar
- Nunca expandir escopo além do que foi solicitado sem aprovação explícita
```

**Development:**
```markdown
## Recursos Instalados

## Restrições

**Banco de dados**
- Nunca alterar schema sem migration versionada
- Migrations sempre revisadas antes de aplicar

**Segurança**
- Nunca commitar variáveis de ambiente (`.env*` sempre no `.gitignore`)
- Chaves de API nunca hardcoded no código

**Git**
- PRs para `main` exigem revisão manual
- Nunca fazer force push em `main`

**Autonomia do Claude**
- Decisões arquiteturais exigem aprovação prévia
- Ações que afetam mais de 5 arquivos exigem apresentação de plano antes de executar
- Nunca expandir escopo além do que foi solicitado sem aprovação explícita
```

**Marketing:**
```markdown
## Recursos Instalados

## Restrições

**Conteúdo**
- Nunca publicar conteúdo sem aprovação explícita
- Assets de marca consultados sempre antes de produzir

**Git**
- PRs para `main` exigem revisão manual
- Nunca fazer force push em `main`

**Autonomia do Claude**
- Decisões editoriais e de posicionamento exigem aprovação prévia
- Ações que afetam mais de 5 arquivos exigem apresentação de plano antes de executar
- Nunca expandir escopo além do que foi solicitado sem aprovação explícita
```

**AI Builder:**
```markdown
## Recursos Instalados

## Restrições

**Autonomia do Claude**
- Decisões que impactam estrutura do projeto exigem aprovação prévia
- Ações que afetam mais de 5 arquivos exigem apresentação de plano antes de executar
- Nunca expandir escopo além do que foi solicitado sem aprovação explícita
```

#### Fragmentos padrão

Incluir ao final do arquivo, nesta ordem, cada seção separada por `---`:

**Fragmento 1 — Idioma e Nomenclatura:**
```markdown
---

## Idioma e Nomenclatura

### Comunicação e Documentação

- Todo conteúdo de chat, documentação e markdown em **pt-BR**
- Acentuação obrigatória: `não` (nunca `nao`), `você` (nunca `voce`), `próximo` (nunca `proximo`)
- Termos técnicos, nomes de frameworks e metodologias permanecem em inglês

### Código

- Identificadores (variáveis, funções, classes, módulos) em **inglês**
- Comentários inline e docstrings em **pt-BR**
- Strings voltadas ao usuário final em **pt-BR**

### Nomenclatura de Arquivos e Diretórios

| Contexto | Padrão | Exemplo |
|---|---|---|
| Diretórios | kebab-case | `claude-md/` |
| Arquivos Markdown | kebab-case | `global.md` |
| Arquivos de configuração | kebab-case | `plugin.json` |
| Scripts shell | kebab-case | `pre-tool-use.sh` |
```

**Fragmento 2 — Comunicação:**
```markdown
---

## Comunicação

### Tom e Estilo

- Linguagem profissional, neutra e objetiva
- Respostas curtas e diretas ao ponto
- Sem emojis, floreios, reforços emocionais ou chamadas motivacionais
- Sem espelhamento de comunicação do usuário
- Sem transições decorativas entre seções

### Formato de Respostas

- Entregue apenas o necessário para avançar o trabalho
- Para perguntas exploratórias: resposta direta em 2-3 frases com recomendação e tradeoff principal
- Para tarefas: execute e reporte resultado — não narre o processo
- Ao referenciar código: cite `arquivo:linha` para navegação direta

### O que Eliminar

- Resumos do que acabou de ser feito ("fiz X, Y e Z")
- Perguntas brandas ("posso ajudar com mais alguma coisa?")
- Confirmações desnecessárias do que o usuário disse
- Comentários sobre a qualidade da pergunta ou tarefa
```

**Fragmento 3 — Protocolo de Execução:**
```markdown
---

## Protocolo de Execução

### Diretrizes obrigatórias

- **Aprovação antes de executar**: nunca executar um plano sem aprovação explícita do usuário. Apresentar o plano, aguardar confirmação, só então agir.
- **Escopo exato**: executar apenas o que foi solicitado. Qualquer adição ao escopo exige aprovação prévia.

### Leitura e diagnóstico

Ações de leitura e observação nunca precisam de confirmação: ler arquivos, executar `git status`, `git log`, `ls`, `find`, `grep` e equivalentes. Não alteram estado — podem ser feitas a qualquer momento.

### Comandos explícitos do usuário

Quando o usuário diz o que fazer ("crie o arquivo X", "renomeie Y para Z"), o pedido é a aprovação. Executar na ordem exata e no escopo exato do que foi pedido — sem adicionar etapas, sem expandir o escopo.

### Planos e ações irreversíveis

Sempre apresentar antes de executar e aguardar aprovação explícita quando:
- Claude propõe uma sequência de ações não solicitada pelo usuário
- A ação é irreversível: deletar arquivos, push, deploy, alterações em banco ou serviços externos
- O impacto afeta mais de 5 arquivos ou envolve dependências externas

### Ambiguidade

Quando a tarefa for ambígua ou o escopo não estiver claro:
1. Declarar o entendimento em uma frase
2. Aguardar confirmação antes de prosseguir
3. Nunca assumir e executar

### Sugestões não solicitadas

Apresentar e aguardar aprovação explícita. Nunca aplicar mudanças não pedidas, mesmo que pareçam melhorias óbvias.
```

**Fragmento 4 — Protocolo Anti-Alucinação:**
```markdown
---

## Protocolo Anti-Alucinação

### Regra Principal

Verificar antes de afirmar. Nenhuma informação sobre o estado do sistema, arquivos ou código deve ser declarada sem evidência obtida via ferramentas na sessão atual.

### Ao Compartilhar Resultados

- Citar a evidência exata: arquivo, linha ou comando que gerou a informação
- Nunca assumir que um arquivo, função ou configuração existe sem lê-lo primeiro
- Memórias de sessões anteriores são ponto de partida, não verdade — verificar antes de usar

### Quando Faltam Dados

1. Listar as fontes consultadas
2. Declarar explicitamente a limitação: "Não encontrei evidências de..."
3. Solicitar o input mínimo necessário para prosseguir

### Proibido

- Inventar nomes de funções, arquivos, flags ou configurações
- Assumir o estado do sistema sem confirmação via ferramenta
- Afirmar que algo "funciona" ou "existe" sem ter verificado na sessão atual
- Ocultar incertezas ou limitações identificadas
```

**Fragmento 5 — Uso de Ferramentas:**
```markdown
---

## Uso de Ferramentas

### Hierarquia de Ferramentas

1. Ferramentas dedicadas têm prioridade sobre Bash (Read, Edit, Write)
2. Bash apenas para operações exclusivas de shell
3. Agent para delegação de tarefas que poluiriam o contexto principal

### Regras de Arquivo

- Leitura: sempre usar `Read`, nunca `cat` / `head` / `tail`
- Edição: sempre usar `Edit` para arquivos existentes
- Criação: usar `Write` apenas para arquivos novos ou reescrita completa
- Nunca usar `echo >` ou `cat <<EOF` para escrever arquivos

### Paralelismo

- Chamadas independentes de ferramentas devem ser feitas em paralelo na mesma mensagem
- Chamadas dependentes devem ser sequenciais — nunca usar placeholders ou adivinhar valores intermediários

### Bash

- Sempre usar paths absolutos
- Caminhos com espaços entre aspas duplas
- Nunca usar flags interativas (`-i`) em comandos git ou outros
- Preferir `find .` ao invés de `find /` para evitar varredura completa do sistema
```

### 5.3 — Gerar `.claude/rules/frontmatter.md`

Gerar com a ferramenta Write, literalmente como abaixo. A norma de frontmatter não vive no `CLAUDE.md`: é procedimento de um domínio específico, e como regra escopada por `paths` só entra em contexto quando o Claude toca um recurso — em vez de custar contexto em toda sessão.

O bloco `paths` no topo **é** frontmatter, e aqui é lido: `.claude/rules/` é um dos dois lugares onde o Claude Code interpreta YAML no topo do arquivo.

````markdown
---
paths:
  - ".claude/**/*.md"
---

# Frontmatter de recurso

Recurso do AmFlow é markdown com manifesto no topo. **Skill segue norma própria** — a spec Agent
Skills, na seção seguinte. Agent, command e hook seguem a tabela desta.

## Agent, command e hook

```yaml
# about
name: resource-name
type: agent                   # agent | command | hook
project: ""
description: ""
tags: []

# history
author: ""
author_id: ""                 # uuid do usuário autenticado — o Builder preenche na Fase 0
created: ""                   # YYYY-MM-DD
status: draft
version: 1.0.0
updated: ""                   # YYYY-MM-DD

# system
scope: project                # global | project
auto_load: false
dependencies: []
```

Recurso publicável ganha a seção `hub`, preenchida por `/amflow-builder:publish` e
`/amflow-builder:publish-status` — nunca à mão:

```yaml
# hub
hub_id: ""                    # uuid atribuído pelo Hub na primeira submissão
source: ""                    # hub/<tipo>/<nome>@<versão> | local
price: 0                      # centavos — 0 é gratuito; definido pelo Creator
```

`auto_load: true` é exceção — só para recurso necessário em toda sessão.

## Skill

O `SKILL.md` segue a [especificação Agent Skills](https://agentskills.io/specification). A tabela
acima **não vale para skill**, e frontmatter de skill escrito a partir dela é rejeitado no submit.

**Três regras estruturais:**

1. **Só o `SKILL.md` tem frontmatter.** Arquivo em `scripts/`, `references/`, `assets/` ou
   `templates/` não tem. A norma alcança o arquivo, não a pasta.
2. **O topo aceita só os campos da spec.** `name` e `description` são obrigatórios; `license` é
   obrigatório no AmFlow; `compatibility` e `allowed-tools` entram só com requisito real. Campo em
   valor default não se escreve — omite-se.
3. **Dado do AmFlow vive em `metadata`, nunca no topo**, com prefixo `amflow-` em kebab-case e
   **valor sempre string** — a spec define `metadata` como mapa de string para string, e valor que
   não seja string é descartado.

```yaml
---
name: nome-da-skill           # igual ao nome do diretório
description: o que faz e quando usar
license: ""
metadata:
  amflow-version: "1.0.0"
  amflow-status: draft
  amflow-author: ""
  amflow-author-id: ""
  amflow-updated: "YYYY-MM-DD"
  amflow-tags: tag-um tag-dois
  amflow-dependencies: skill/nome@1.0.0
---
```

Lista é separada por espaço; dependência é `type/name@version`. `amflow-hub-id` aparece após a
primeira publicação; `amflow-source` existe só na cópia instalada.

**`amflow-status` — oito valores:** `draft`, `review` (Creator escreve), `pending_review`
(o `publish` escreve), `changes_requested`, `rejected`, `published`, `suspended`
(o `publish-status` escreve), `deprecated` (Creator). Skill nova nasce em `draft`.

**Uma forma só.** Declare os seis da spec e as extensões do Claude Code que carreguem comportamento.
Medido em 2026-08-28: as quatorze extensões atravessam o upload do Cowork sem recusa.

Não escrever frontmatter de skill à mão: usar `/amflow-builder:build`.

## O que não é frontmatter

- **`CLAUDE.md`** — o Claude Code não interpreta YAML no topo dele.
- **Módulo** — o manifesto é o `module.json` ao lado do `MODULE.md`.
- **Arquivo interno de skill** — ver regra 1 acima.
````

### 5.4 — Criar `settings.json`

Verificar se `~/.claude-plugin/defaults/settings.json` existe:
- Existe → copiar para `<pasta>/.claude/settings.json`
- Não existe → criar `<pasta>/.claude/settings.json` com conteúdo `{}`

Se `<pasta>/.claude/settings.json` já existir → manter sem sobrescrever.

## Pós-execução

Exibir ao usuário:

```
[ok] Projeto '<nome>' configurado em <pasta>

Criados:
  .claude/CLAUDE.md
  .claude/rules/frontmatter.md
  .claude/settings.json
  .claude/skills/
  .claude/agents/
  .claude/hooks/
  .claude/commands/
  .claude/plugins/
  .claude/modules/
  .claude/rules/

Próximos passos:
  /amflow-builder:start   — abrir a sessão neste projeto
  /amflow-builder:build   — criar recursos para o projeto
  /amflow-builder:publish — publicar recursos no Hub
```

## Restrições

- Verificar existência da pasta antes de criar qualquer coisa.
- Nunca criar `.claude/CLAUDE.md` se já existir.
- Nunca sobrescrever `.claude/settings.json` nem `.claude/rules/frontmatter.md` se já existirem.
- O `CLAUDE.md` gerado não tem frontmatter.

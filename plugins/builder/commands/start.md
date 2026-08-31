---
# about
name: start
type: command
project: AmFlow
description: Abre a sessão no projeto atual — relê o CLAUDE.md, lista as regras e os recursos disponíveis, e devolve um briefing curto do estado
tags: [start, onboarding, sessao, contexto, creator]

# history
author: Bortoli
created: 2026-08-30
status: draft
version: 1.0.0
updated: ""

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-builder:start

Abre a sessão no projeto atual: relê as instruções, verifica o estado e devolve um briefing curto.

**Sem Fase 0.** Este comando não chama o MCP: é leitura de disco, sem rede e sem autenticação.
Funciona offline.

**Por que reler o `CLAUDE.md` se ele já carregou.** Ele carrega, sim — como mensagem de usuário logo
após o system prompt. Numa sessão que já andou, isso fica longe do ponto onde o trabalho acontece. A
releitura recoloca as instruções adjacentes à tarefa, e é o gesto que na prática muda a qualidade da
execução. O custo é o arquivo entrar duas vezes no contexto, e é aceito de propósito.

## Processo

Executar na ordem. Tudo é leitura — nada aqui altera estado, nada pede confirmação.

### 1 — Instruções do projeto

Ler `.claude/CLAUDE.md` com a ferramenta Read.

Ausente → dizer que o projeto não está configurado e sugerir `/amflow-builder:new-project`. Seguir
para os passos 3 e 4 assim mesmo: branch e estrutura ainda informam.

Se houver `CLAUDE.md` na raiz do projeto além do de `.claude/`, ler os dois — ambos carregam, e o
conflito entre eles é a primeira coisa que vale reportar.

### 2 — Regras

```bash
find .claude/rules -maxdepth 1 -name '*.md' 2>/dev/null
```

Listar os nomes, sem abrir. Regra com `paths` no topo só entra em contexto quando o Claude lê um
arquivo que casa com o glob — saber que ela existe antes de tocar o arquivo muda o comportamento.

**Sempre `find`, nunca glob de shell.** No zsh, glob sem correspondência é erro que aborta o comando
inteiro — e `2>/dev/null` esconde a mensagem sem impedir a falha. Um `ls .claude/*/` numa pasta vazia
derruba a listagem toda, inclusive a parte que tinha resultado.

### 3 — Estado do repositório

```bash
git branch --show-current 2>/dev/null
git status --short 2>/dev/null
```

Fora de um repositório git, os dois falham em silêncio — omitir a linha de estado no briefing, sem
tratar como erro.

### 4 — Topo do projeto

```bash
find . -mindepth 1 -maxdepth 1 -type d -not -name '.*' -not -name node_modules
```

Só o primeiro nível. Não descer: o objetivo é saber onde as coisas ficam, não inventariar o
repositório.

### 5 — Recursos do projeto

Um `find` por tipo — pasta ausente ou vazia devolve nada e não afeta os outros:

```bash
for t in skills agents hooks commands modules; do
  n=$(find ".claude/$t" -mindepth 1 -maxdepth 1 -not -name '.*' 2>/dev/null | wc -l | tr -d ' ')
  echo "$t: $n"
done
```

O `-not -name '.*'` não é zelo: o `/amflow-builder:new-project` põe um `.gitkeep` em cada pasta para
que elas sobrevivam ao primeiro commit. Sem o filtro, todo projeto recém-criado é reportado com um
recurso de cada tipo, e nenhum existe.

## Saída

Um briefing de 10 a 15 linhas. O `CLAUDE.md` inteiro entra no contexto pela leitura do passo 1 — o
que vai para a tela é o resumo, nunca o arquivo.

```
<nome do projeto> — <o que ele é, numa linha>
<uma frase: o que ele faz, para quem, ou o que o distingue>

Branch <branch>, <estado do working tree>        (omitir se não for repositório git)
Topo: <pastas do primeiro nível>
Regras: <arquivos em .claude/rules/, ou "nenhuma">
Recursos: <n> skills, <n> agents, <n> commands, <n> hooks, <n> modules

O que mais pesa aqui:
- <restrição do CLAUDE.md>
- <restrição do CLAUDE.md>
- <restrição do CLAUDE.md>
```

As duas primeiras linhas saem da leitura do passo 1 — do título e da visão geral —, **não de campo
de frontmatter**. O `CLAUDE.md` não tem frontmatter, e projeto configurado à mão pode não ter nem
seção de identidade: escrever as duas linhas a partir do que o arquivo disser é sempre possível,
depender de um campo não é.

As três restrições são escolha de julgamento, não as três primeiras do arquivo: as que mais mudariam
o que o Claude faria a seguir neste projeto. Projeto sem restrição declarada → omitir o bloco inteiro
em vez de preencher com genérico.

Terminar aqui. Não propor trabalho, não perguntar o que o usuário quer fazer — ele já sabe, e o
comando existe para orientar, não para conduzir.

## Restrições

- Somente leitura. Nunca escrever, nunca alterar estado, nunca chamar o Hub.
- Nunca despejar o conteúdo do `CLAUDE.md` na tela — ele já está no contexto.
- Não checar atualização de recurso: é trabalho do `/amflow-worker:hub-check`, e depende de rede e
  de sessão autenticada. O `start` funciona offline.
- Ausência de arquivo ou de pasta nunca é erro — é informação. Reportar e seguir.

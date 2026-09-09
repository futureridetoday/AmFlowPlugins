---

## Instrução para o comprador — ligar `important.md` ao `CLAUDE.local.md`, e o `.gitignore`

O Worker tem `hooks/` (`path-safety`, `hard-memory-guard`) e os comandos `install`/`get`, mas nenhum
dos quatro grava arquivo neste caminho: `path-safety` só nega escritas em alvos sensíveis,
`hard-memory-guard` só bloqueia o `Stop` como lembrete, e `install`/`get` se restringem, por
contrato do próprio comando, a `<projeto>/.claude/` ou `~/.claude/` — `CLAUDE.local.md` e
`.gitignore` ficam fora disso. Não existe mecanismo de instalação que escreva por você. Depois de
usar `/amflow-worker:memory --important <texto>` pelo menos uma vez, aplique os dois passos abaixo
no projeto onde o plugin está instalado — uma vez só.

### 1. `./CLAUDE.local.md`, na raiz do projeto

Cole o bloco abaixo em `./CLAUDE.local.md` — a forma do import é a completa, porque este arquivo
está na raiz, e não dentro de `.claude/` (o inverso do Builder e do repo AmFlow):

## Memória do usuário

@.claude/memory/important.md

`.claude/memory/notes.md` é a memória curada pelo usuário. Leia sob demanda, quando ele pedir —
nunca em toda sessão. Nunca reorganize, resuma nem reescreva o arquivo por conta própria: a entrada
é literal até o usuário decidir o contrário. Promova uma entrada a regra no `CLAUDE.md` apenas
quando ele pedir explicitamente.

### 2. `.gitignore`, na raiz do projeto

Garanta a entrada `CLAUDE.local.md` no `.gitignore` do projeto, sem duplicar se já existir —
`CLAUDE.local.md` contém memória pessoal do comprador e nunca deve ser commitado.

---
# about
name: install-module
type: skill
project: AmFlow
description: Instala um módulo numa skill e propaga atualizações de módulo para todas as skills que o consomem — copia a árvore do módulo, escreve a região `modules` do SKILL.md e registra a versão em `metadata`. Use when o Creator quer adicionar um módulo a uma skill, atualizar um módulo já instalado, ou propagar uma nova versão de módulo para seus consumidores; invocada por /amflow-builder:install-module ou pelo Claude ao detectar intenção de instalar ou propagar módulo
tags: [module, install, update, propagate, skill, creator]

# history
author: Bortoli
created: 2026-08-14
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

# Install Module

Instala um módulo numa skill, e propaga uma nova versão do módulo para todas as skills que já o consomem.

**Instalar e propagar são a mesma operação.** Propagar é instalar de novo, em cada consumidor. Não há caminho de código separado, e não deve haver: qualquer regra que valha só para um dos dois vira divergência silenciosa.

## Quando usar

- O Creator quer adicionar um módulo existente a uma skill
- O Creator subiu a versão de um módulo e quer levá-la a quem o usa
- Invocada por `/amflow-builder:install-module`
- Claude detecta intenção de instalar módulo em skill, ou de propagar versão de módulo

## Não usar quando

- **O módulo ainda não existe** — criar é `/amflow-builder:build`, tipo `module`. Esta skill não cria módulo.
- O que se quer é editar o comportamento do módulo — isso se faz na origem, `<raiz-de-recursos>/modules/<nome>/`, e chega aos consumidores por uma propagação depois.

## Conceitos

### Raiz de recursos

É o diretório que contém `skills/`. Partindo da skill alvo, sobe-se dois níveis: `<raiz>/skills/<skill>/` → `<raiz>`.

| Topologia | Raiz de recursos |
|---|---|
| Projeto | `.claude/` |
| Plugin | `plugins/<plugin>/` |
| Repositório de skills | a raiz do repositório |

Não há configuração a ler nem variável de ambiente envolvida. Se o diretório em que a skill vive não tem uma irmã `skills/` acima, o caminho está errado — pare e informe.

### Origem e cópia

| | Caminho |
|---|---|
| **Origem** | `<raiz-de-recursos>/modules/<nome>/` |
| **Cópia instalada** | `<skill>/modules/<nome>/` |
| **Configuração da skill** | `<skill>/config/<nome>.json` |

### O contrato no `SKILL.md`

Dois lugares, e só esses dois:

**A região no corpo** — uma linha por módulo, com ponteiro direto:

```markdown
<!-- modules:start -->
## Módulos instalados

- **task-flow@1.2.0** — lista de tarefas com estado. Como usar: `modules/task-flow/MODULE.md`
<!-- modules:end -->
```

**A chave no `metadata` do frontmatter** — uma por módulo:

```yaml
metadata:
  amflow.module.task-flow: "1.2.0"
```

A chave é `amflow.module.<nome>` e o valor é a versão, string entre aspas. É essa chave que a propagação usa para descobrir os consumidores, então a forma não é negociável.

## Instruções

### Instalar `<módulo>` em `<skill>`

1. Resolver a raiz de recursos a partir da skill alvo, e localizar a origem em `<raiz-de-recursos>/modules/<nome>/`. Origem inexistente → encerrar: `Módulo não encontrado: <caminho> — crie-o com /amflow-builder:build, tipo module`.
2. Ler `module.json` da origem → `name` e `version`. `name` diferente do nome do diretório → encerrar e informar a divergência.
3. Copiar **a árvore inteira** da origem para `<skill>/modules/<nome>/`, `tests/` incluído. Se o diretório de destino já existe, apagá-lo antes — a cópia é gerada, e mesclar produziria um estado que não corresponde a versão nenhuma.
4. Se a origem tem `config.example.json` **e** `<skill>/config/<nome>.json` **não** existe, copiar o exemplo para lá. **Se já existe, não tocar.**
5. Escrever a região `modules` do `SKILL.md`: uma linha por módulo instalado, no formato `- **<nome>@<versão>** — <uma frase> Como usar: \`modules/<nome>/MODULE.md\``. Preservar as linhas dos outros módulos.
6. Escrever `amflow.module.<nome>: "<versão>"` em `metadata`, no frontmatter:
   - Bloco `metadata:` já ativo → acrescentar ou atualizar a chave dentro dele.
   - Só o exemplo comentado do template (`# metadata:` / `#   amflow.module....`) → **substituí-lo no lugar** pelo bloco real. Nunca deixar os dois: um bloco ativo com o exemplo comentado logo abaixo confunde quem for editar depois, e convida a mexer no lugar errado.
   - Nem um nem outro → criar o bloco no fim da seção de campos opcionais do frontmatter.
7. Relatar: arquivos escritos, versão instalada, e se `config/<nome>.json` foi criado ou preservado.

> **O passo 4 é a única assimetria entre instalar e propagar, e ela vive aqui.** Sem a guarda "não tocar se já existe", propagar apagaria a configuração que o Creator preencheu — e propagar é literalmente repetir esta sequência. Não escreva a exceção do lado do propagar; ela não existe lá.

### Propagar `<módulo>`

1. Confirmar que a origem tem a versão nova — ler `version` do `module.json`. Se o Creator ainda não subiu a versão, perguntar antes de seguir: propagar sem mudar a versão deixa os consumidores declarando uma versão que já não descreve o conteúdo.
2. Achar os consumidores: procurar `amflow.module.<nome>` em todo `SKILL.md` sob `<raiz-de-recursos>/skills/`.
3. Para cada consumidor, executar a sequência de **Instalar** inteira, sem exceção e sem pular passo.
4. Relatar por skill: versão anterior → versão nova, e se a configuração foi preservada.

Nenhum consumidor encontrado → dizer isso explicitamente, e não tratar como erro. Módulo sem consumidor é estado válido.

## Invariantes

- **`<skill>/modules/<nome>/` pertence ao módulo e é descartável.** Nada ali é editado à mão, e a propagação apaga e recopia sem perguntar. Se o Creator disser que editou algo lá, a mudança vai para a origem — nunca preserve a edição na cópia.
- **`<skill>/config/<nome>.json` pertence à skill.** Criado uma vez, nunca sobrescrito por instalação nenhuma.
- **Fora do diretório do módulo, escrever só em dois lugares:** a região `modules` do `SKILL.md` e a chave em `metadata`. Nenhuma outra linha da skill é tocada.
- **Ponteiro direto, um salto.** Cada linha da região aponta para o `MODULE.md` daquele módulo pelo caminho completo. Nunca substituir as linhas por "veja `modules/`" — o agente que ler a skill precisa do caminho, não do convite a navegar.
- **Instalar e propagar compartilham a sequência.** Regra nova entra nos dois, ou não entra.

## Output

Ao instalar:

```
Instalado: <nome>@<versão> em <skill>
  <skill>/modules/<nome>/          árvore copiada (N arquivos)
  <skill>/config/<nome>.json       criado a partir do exemplo | preservado | não se aplica
  <skill>/SKILL.md                 região modules e metadata atualizados
```

Ao propagar, uma linha por consumidor, mais o total:

```
Propagado: <nome> 1.2.0 → 1.3.0
  skills/audience-segmentation     ok · config preservada
  skills/report-builder            ok · config preservada
2 consumidores atualizados
```

## Restrições

- Um módulo por execução ao instalar. Propagar toca vários consumidores, mas de um módulo só.
- Nunca criar módulo — se a origem não existe, encerrar e apontar `/amflow-builder:build`.
- Nunca editar o conteúdo do módulo durante a instalação. A cópia é fiel à origem, byte a byte.

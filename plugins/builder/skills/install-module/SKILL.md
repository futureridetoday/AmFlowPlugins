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

É o diretório que contém `skills/`. Partindo da skill alvo, sobe-se **dois níveis**: em
`<raiz>/skills/<skill>/`, o pai da skill é `skills/` e o avô é a raiz.

Duas checagens, e as duas precisam passar: **o diretório-pai da skill chama-se `skills/`**, e
`<raiz>/modules/` existe. Falhando qualquer uma, o caminho está errado — pare e informe.

| Topologia | Raiz de recursos |
|---|---|
| Projeto | `.claude/` |
| Plugin | `plugins/<plugin>/` |
| Repositório de skills | a raiz do repositório |

Não há configuração a ler nem variável de ambiente envolvida.

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
2. Ler `module.json` da origem → `name`, `version` e `description`. `name` diferente do nome do diretório → encerrar e informar a divergência. `version` ou `description` ausente → encerrar: os três são obrigatórios, e os três são lidos para agir.
   **`description` sem pontuação final** (`.`, `!` ou `?`) → encerrar: `description do módulo <nome> não termina em pontuação — corrija o module.json na origem`. Ela é emendada à frase `Como usar:` no passo 7, e sem pontuação as duas colam numa frase só. **Recusar em vez de normalizar** é deliberado: normalizar em memória faria a linha do `SKILL.md` deixar de ser cópia literal do `module.json` instalado ao lado, e as duas regras não podem valer ao mesmo tempo.
3. Copiar a árvore da origem para `<skill>/modules/<nome>/`, `tests/` incluído. Se o diretório de destino já existe, apagá-lo antes — a cópia é gerada, e mesclar produziria um estado que não corresponde a versão nenhuma. Criar os diretórios intermediários que faltarem.
   **Excluir da cópia:**
   - `__pycache__/`, `*.pyc`, `*.pyo`, `.DS_Store` — artefato gerado. Difere entre máquinas, e copiá-lo faria duas instalações da mesma versão produzirem árvores diferentes.
   - `config.example.json` — ele **vira** `<skill>/config/<nome>.json` no passo 5, que é da skill e editável. Mantê-lo também dentro de `modules/<nome>/`, que é descartável, poria o mesmo conteúdo em dois caminhos com donos opostos — e é justamente a confusão de propriedade que os *Invariantes* existem para impedir.

   `module.json` **fica** na cópia, apesar de repetir a versão que vai para o `metadata`. Os dois não podem divergir, porque a cópia inteira é substituída a cada propagação; e tê-lo ali permite saber que versão está instalada sem abrir o `SKILL.md`.
4. **Verificar a cópia antes de seguir.** Comparar **conteúdo**, arquivo a arquivo, entre a origem e o destino, desconsiderando as exclusões do passo 3. Divergência → refazer a cópia e comparar de novo; persistindo, encerrar sem tocar no `SKILL.md`.

   > **Este passo existe por um quase-acidente medido.** Numa execução real, `rsync -a` **pulou o `module.json`** porque origem e destino tinham o mesmo tamanho e a mesma mtime — a heurística padrão da ferramenta. A propagação teria terminado com o `SKILL.md` anunciando a versão nova e o `module.json` instalado ainda na antiga, em silêncio. O `module.json` é o arquivo mais exposto a isso: entre duas versões, muitas vezes a única mudança é um dígito, e o tamanho não muda. Comparar por conteúdo, nunca por tamanho e data — `rsync` precisa de `--checksum`, e qualquer cópia precisa da conferência.
5. Se a origem tem `config.example.json` **e** `<skill>/config/<nome>.json` **não** existe, copiar o exemplo para lá — **criando o diretório `config/` se ele não existir**. Se o arquivo já existe, não tocar.
6. **Se o config já existia, comparar as chaves** do `config.example.json` da origem com as do config da skill, **sem alterar nada**. Chave presente no exemplo e ausente no config → relatar como `configuração possivelmente incompleta`; chave no config e ausente no exemplo → relatar como `configuração com chave que o módulo não declara mais`. Não é erro e não bloqueia: config divergente do exemplo costuma ser exatamente o que a skill quis. Mas uma versão nova que passe a exigir uma chave deixaria o consumidor quebrado com a propagação reportando "config preservada" como se estivesse tudo bem — e é a única forma de o Creator saber sem abrir os dois arquivos.
7. Escrever a região `modules` do `SKILL.md`. A região inteira é substituída, e o que fica dentro dela é:

   ```markdown
   <!-- modules:start -->
   ## Módulos instalados

   - **<nome>@<versão>** — <description do module.json> Como usar: `modules/<nome>/MODULE.md`
   <!-- modules:end -->
   ```

   - **O cabeçalho `## Módulos instalados` fica dentro da região**, e é reescrito junto. Fora dela, ele sobreviveria a uma remoção de módulo e deixaria um título órfão.
   - **A frase é a `description` do `module.json`, copiada literalmente** — nunca redigida pelo agente. Redação livre faz duas instalações do mesmo módulo produzirem linhas diferentes, e faz cada propagação reescrever a linha sem que nada tenha mudado.
   - Uma linha por módulo, **ordenadas alfabeticamente pelo nome**. A região é substituída por inteiro, então **ler as linhas que já estão lá antes de escrever** e reemiti-las junto com a nova — trocando apenas a do módulo que está sendo instalado. Linha preexistente fora do formato → preservar como está e relatar ao final; nunca descartar linha que não se soube ler.
   - **Se a região não existe no `SKILL.md`** — o caso de toda primeira instalação —, criá-la **no fim do arquivo**, precedida de uma linha em branco. Nunca no meio: a posição precisa ser previsível para que a região seja localizável sem varrer o documento, e o fim é a única posição que não depende da estrutura da skill.
8. Escrever `amflow.module.<nome>: "<versão>"` em `metadata`, no frontmatter:
   - Bloco `metadata:` já ativo → acrescentar ou atualizar a chave dentro dele.
   - Só o exemplo comentado do template (`# metadata:` / `#   amflow.module....`) → **substituí-lo no lugar** pelo bloco real. Nunca deixar os dois: um bloco ativo com o exemplo comentado logo abaixo confunde quem for editar depois, e convida a mexer no lugar errado.
   - Nem um nem outro — o caso de qualquer skill que não venha do template atual → criar o bloco **na última linha do frontmatter**, antes do `---` de fechamento, separado do que vem acima por uma linha em branco. Como o fim da região, é a única posição que não depende de a skill ter alguma seção específica.
9. Relatar: arquivos escritos, versão instalada, o estado do `config/<nome>.json` — **criado** (a partir do exemplo), **preservado** (já existia), ou **não se aplica** (a origem não tem `config.example.json`) — e qualquer divergência de chave que o passo 6 tenha encontrado. São os mesmos três estados do bloco *Output*.

> **O passo 5 é a única assimetria entre instalar e propagar, e ela vive aqui.** Sem a guarda "não tocar se já existe", propagar apagaria a configuração que o Creator preencheu — e propagar é literalmente repetir esta sequência. Não escreva a exceção do lado do propagar; ela não existe lá.

### Propagar `<módulo>`

1. Achar os consumidores: procurar `amflow.module.<nome>` em todo `SKILL.md` sob `<raiz-de-recursos>/skills/`. A versão que cada um declara na chave é a versão instalada nele.
2. Comparar a `version` do `module.json` da origem com a de cada consumidor. **Todos já na versão da origem** → não há o que propagar; dizer isso e encerrar. Origem com versão **anterior** à de algum consumidor → parar e informar: é sinal de que a origem foi revertida ou de que alguém editou o `metadata` à mão.

   > A ordem importa e já esteve errada aqui: este passo era o primeiro e mandava "confirmar que a origem tem a versão nova" lendo só o `module.json` da origem. Lendo só a origem não há o que confirmar — *nova* é relativo ao que os consumidores declaram, e eles só existem depois da busca.

3. **Procurar árvore órfã:** diretório `<skill>/modules/<nome>/` em skill que **não** tem a chave `amflow.module.<nome>`. Não é consumidora pela definição do passo 1, então a propagação não a alcança e ela fica congelada para sempre. Relatar cada uma ao Creator; não corrigir por conta própria — instalar ali é decisão dele, não consequência de uma propagação.
4. Para cada consumidor, executar a sequência de **Instalar** inteira, sem exceção e sem pular passo.
5. Relatar por skill: versão anterior → versão nova, o estado do config nos mesmos três valores do passo 9 de *Instalar*, e qualquer divergência de chave que o passo 6 tenha encontrado.

Nenhum consumidor encontrado → dizer isso explicitamente, e não tratar como erro. Módulo sem consumidor é estado válido.

## Invariantes

- **`<skill>/modules/<nome>/` pertence ao módulo e é descartável.** Nada ali é editado à mão, e a propagação apaga e recopia sem perguntar. Se o Creator disser que editou algo lá, a mudança vai para a origem — nunca preserve a edição na cópia.
- **`<skill>/config/<nome>.json` pertence à skill.** Criado uma vez, nunca sobrescrito por instalação nenhuma.
- **Fora do diretório do módulo, escrever só em dois lugares:** a região `modules` do `SKILL.md` e a chave em `metadata`. Nenhuma outra linha da skill é tocada.
- **Ponteiro direto, um salto.** Cada linha da região aponta para o `MODULE.md` daquele módulo pelo caminho completo. Nunca substituir as linhas por "veja `modules/`" — o agente que ler a skill precisa do caminho, não do convite a navegar.
- **Instalar e propagar compartilham a sequência.** Regra nova entra nos dois, ou não entra.
- **Não tocar `version` nem `updated` da skill.** Instalar módulo não versiona a skill: quem decide que a skill mudou de versão é quem a mantém, e uma instalação que mexesse nesses campos tiraria essa decisão dele. Vale mesmo parecendo que "a skill mudou" — mudou o que o módulo trouxe, não o que a skill é.
- **Não rodar a suíte do módulo depois de copiar.** A cópia é verificada contra a origem no passo 3b, e é isso que a instalação promete. A suíte pode ter runner próprio, dependência externa e tempo de execução que a instalação não controla — rodá-la faria a instalação falhar por motivo que não é dela.

## Output

Ao instalar:

```
Instalado: <nome>@<versão> em <skill>
  <skill>/modules/<nome>/          árvore copiada (N arquivos regulares, sem contar diretórios)
  <skill>/config/<nome>.json       criado a partir do exemplo | preservado | não se aplica
  <skill>/SKILL.md                 região modules e metadata atualizados
```

Ao propagar, uma linha por consumidor, mais o total. O estado do config usa os mesmos três valores de *Instalar*, e a divergência de chave do passo 4b aparece quando houver:

```
Propagado: <nome> 1.2.0 → 1.3.0
  skills/audience-segmentation     ok · config preservada
  skills/report-builder            ok · config preservada · 1 chave nova no exemplo: retention_days
  skills/onboarding                ok · config criado
3 consumidores atualizados

Árvore órfã — tem modules/<nome>/ sem a chave em metadata, e a propagação não a alcança:
  skills/legacy-report
```

Caminhos são relativos à raiz de recursos, nos dois blocos.

## Restrições

- Um módulo por execução ao instalar. Propagar toca vários consumidores, mas de um módulo só.
- Nunca criar módulo — se a origem não existe, encerrar e apontar `/amflow-builder:build`.
- Nunca editar o conteúdo do módulo durante a instalação. Cada arquivo que entra na cópia é idêntico ao da origem, byte a byte — o que a cópia **omite** está enumerado no passo 3, e é a única liberdade que existe. Transformar conteúdo, nunca.

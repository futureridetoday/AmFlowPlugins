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
version: 2.0.0
updated: "2026-08-31"

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

Inicializa a estrutura `.claude/` e cria os arquivos base de um novo projeto AmFlow. Disponível para Creators e Managers com o plugin Builder instalado.

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação (inclusive o survey e qualquer criação de arquivo), chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → o comando segue. Com sessão já ativa, o `me` responde direto e o comando segue sem novo login. Nenhum arquivo gerado carrega o `user_id`: a Fase 0 é o gate de autenticação do plugin, não fonte de carimbo.
- Sem sessão / erro → o conector `amflow-builder` não está autorizado nesta sessão. **Encerre aqui** — não
  prossiga para o survey nem crie qualquer arquivo. Este costuma ser o primeiro comando que o Creator
  roda depois de instalar o plugin: dizer só "autorize" o deixa sem saber o que perdeu. Explique, sem
  passar de um parágrafo curto: o que o comando faria (estrutura `.claude/` e instruções do projeto), que a autorização
  é única e vale para todos os comandos do Builder, e como fazê-la. O "como" depende de onde a sessão
  roda, e dar só um caminho deixa metade dos Creators sem saída: no terminal interativo, `/mcp` e
  autorizar `amflow-builder`; nas demais superfícies — sessão não-interativa, app ou web —, `/mcp` não
  existe, e a autorização sai pelas configurações de conectores da conta. Encerrar com o convite a
  reexecutar `/amflow-builder:new-project`.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

## Survey (Passos 1–4)

Faça uma pergunta por vez, usando o contexto acumulado para gerar sugestões.

### Passo 1 — Pasta do projeto

Executar `pwd` e exibir o caminho atual como sugestão primária. Aceitar "Informar outro caminho" para texto livre.

Com a pasta escolhida, verificar as duas condições que só dependem dela — aqui, e não na execução: as
duas encerram o comando, e encerrar depois do survey desperdiça as perguntas dos Passos 2 a 4.

```bash
test -d "<pasta>"
```
Não existe → encerrar: **"Diretório não encontrado: <pasta>"**

```bash
test -f "<pasta>/.claude/CLAUDE.md"
```
Existe → encerrar: **"Projeto já configurado em <pasta> — execute /amflow-builder:build para criar recursos."**

Encerrar mesmo: não oferecer reconfigurar. Nenhum comando do Builder atualiza um `CLAUDE.md` que já
existe, e oferecer seria prometer o que não há.

### Passo 2 — Nome do projeto

Derivar do último segmento do caminho. O nome não fica só no título do `CLAUDE.md`: o
`/amflow-builder:build` o copia para o campo `project` do frontmatter de todo recurso criado, e dali
ele vai ao Hub na publicação. Pasta com nome composto sugerida crua se propaga por tudo isso.

Oferecer, nesta ordem: o **nome legível derivado** — só quando diferir do literal —, o **literal da
pasta**, e "Informar outro nome".

| Forma da pasta | Sugestão | Exemplo |
|---|---|---|
| Com separador (`-`, `_`, `.`) | trocar por espaço e capitalizar | `nome-do-meu-projeto` → `Nome do Meu Projeto` |
| CamelCase / PascalCase | manter como está | `AmFlow` → `AmFlow` |
| Uma palavra, tudo minúsculo | segmentar, se reconhecer as palavras | `decodeandcode` → `Decode and Code` |

CamelCase fica intacto de propósito: quem escreveu `AmFlow` escolheu aquela forma, e "Am Flow" desfaz
a escolha.

Conectores em minúscula fora da primeira posição, **na língua do próprio nome** — `de`, `do`, `da`,
`dos`, `das`, `e`, `em`, `no`, `na`, `para`, `com` em português; `and`, `of`, `the`, `for`, `in` em
inglês. `decodeandcode` vira `Decode and Code`, não `Decode And Code`.

Nunca inventar palavra que não esteja no nome da pasta. Não reconhecer as palavras de um nome colado
não é erro nem motivo para adivinhar: sugerir o literal e seguir.

A resposta final é gravada em `<nome-projeto>`.

### Passo 3 — Áreas de atuação

Seleção múltipla: de uma a cinco opções.

| Opção | Descrição |
|---|---|
| Branding | identidade de marca, naming, verbal e visual |
| UX & UI Design | pesquisa, fluxos, interface e protótipo |
| Design System | biblioteca de componentes, tokens e documentação de uso |
| Development | aplicações, APIs, plataformas e sistemas |
| Social Media | estratégia, campanhas e produção de conteúdo |

O marcado é gravado em `<areas-de-atuacao>`, separado por vírgula na ordem da tabela.

A lista cresce. Cada área é uma chave de composição — quando houver instrução específica por área,
ela entra por aqui, e é por isso que o campo é lista e não escolha única.

**O tipo não é perguntado.** Ele é literal, e diz o que o projeto produz:
`Recursos para Claude Code — skills, agents, commands e hooks`. O `new-project` é exclusivo do Builder, e o
Builder produz recursos para o Worker — perguntar teria uma resposta só. Está escrito por extenso, e
não como rótulo de categoria, porque quem lê a tabela é um Claude abrindo o projeto pela primeira
vez: `AI Builder` admitia tanto "constrói modelos de IA" quanto "usa IA", e não citava Claude Code
nem skill.

O que varia — e o que este passo captura — é onde esses recursos vão atuar: uma skill de naming e uma
de migration de banco são as duas recursos para o Claude Code, e não se parecem em mais nada.

### Passo 4 — Descrição do projeto

Faça de 1 a 3 perguntas objetivas, uma por vez, para entender o projeto — o que ele faz, para quem, e
qual o objetivo principal. As perguntas saem de `<areas-de-atuacao>`: o que se pergunta a um projeto
de Branding não é o que se pergunta a um de Development, e área já marcada é contexto que não precisa
ser perguntado de novo. Use as respostas acumuladas, mais nome e áreas, para propor uma descrição de
uma frase.

Exibir a descrição proposta como sugestão primária e aceitar "Outro (digitar)" para texto livre. A resposta final é gravada em `<descricao>`.

Guardar também o que foi perguntado e o que foi respondido, em `<perguntas-respostas>`: uma linha por
pergunta feita, na forma `- **<pergunta>** — <resposta>`. A descrição é uma destilação, e destilar
perde — o que o Creator disse sobre o projeto é a informação mais rica que este comando coleta, e sem
isto ela morre no fim do survey.

Duas regras para essas linhas. **Transcrever, não reescrever:** a resposta entra como o Creator a
deu, corrigida só no óbvio. **Produto e propósito, não arquitetura:** a checagem de `/doctor` propõe
cortar de um `CLAUDE.md` o que o Claude deriva do código — layout de diretórios, dependências,
panorama de arquitetura. O que o projeto faz e para quem não é derivável e fica; se uma resposta
descambar para como o sistema é montado, ela é candidata a corte já no dia seguinte.

Uma pergunta só respondida → uma linha só. Nunca preencher as outras.

## Execução (Passo 5)

### 5.1 — Criar estrutura

```bash
for d in skills agents hooks commands plugins modules rules; do
  mkdir -p "<pasta>/.claude/$d"
  touch "<pasta>/.claude/$d/.gitkeep"
done
```

O `.gitkeep` existe porque o git não versiona diretório vazio: sem ele, o Creator faz o primeiro
commit e as sete pastas somem do repositório — quem clonar recebe só os arquivos, e a estrutura que a
pós-execução anunciou não é a que o time recebe. Nada quebra em execução, já que o Write recria o
diretório pai; o que se perde é a estrutura combinada.

Arquivo já existente não é tocado: `touch` num `.gitkeep` que já está lá não muda conteúdo.

### 5.2 — Gerar `.claude/CLAUDE.md`

Gerar com a ferramenta Write. O arquivo é composto por: seções fixas → fragmentos padrão.

**Sem frontmatter.** O `CLAUDE.md` não é manifesto de recurso: o Claude Code o entrega como mensagem de usuário e não interpreta bloco YAML no topo — frontmatter ali é texto que consome contexto em toda sessão sem ser lido por nada. O arquivo começa direto no `#` do título.

**O nome do projeto no corpo, não em frontmatter.** A linha "Nome do projeto" da tabela Identidade é
o que o `/amflow-builder:build` lê para preencher o campo `project` do frontmatter de todo recurso.
Fica no corpo porque frontmatter no `CLAUDE.md` não é lido por nada — e fica declarado, em vez de
inferido do título, porque título é prosa: quem editar o `#` à mão, ou configurar o projeto sem este
comando, quebraria a leitura em silêncio.

**O que substituir, e o que copiar como está.** Nos blocos abaixo, só quatro marcadores vêm do
survey: `<nome-projeto>`, `<areas-de-atuacao>`, `<descricao>` e `<perguntas-respostas>`. O tipo de
projeto é literal e não vem de pergunta nenhuma, e `<pasta>` não entra aqui — ela é destino de
escrita, usada no 5.1, no 5.5 e na pós-execução, nunca conteúdo do arquivo.

Todo o resto entre `<>` é conteúdo do arquivo gerado, endereçado ao Claude que vai ler aquele
`CLAUDE.md` depois — `<nome>` na tabela "Onde cada recurso vive" é o nome de um recurso qualquer, não
o deste projeto. Substituí-lo produz um `CLAUDE.md` afirmando que as skills do projeto vivem em
`.claude/skills/<nome-projeto>/`, que é falso e não se parece com erro.

#### Seções fixas

```markdown
# <nome-projeto> — Instruções do Projeto

## Identidade

| Campo | Valor |
|---|---|
| Nome do projeto | <nome-projeto> |
| Tipo de projeto | Recursos para Claude Code — skills, agents, commands e hooks |
| Áreas de atuação | <areas-de-atuacao> |

## Visão Geral

<descricao>

<perguntas-respostas>

## Recursos AmFlow

Recurso novo — skill, agent, command, hook, plugin, workflow ou module — se cria por
`/amflow-builder:build`, que aplica o template e o frontmatter da norma vigente. É o
que torna o recurso publicável: o Hub recusa submissão com `metadata` incompleto.

Pedido de criação que chegue sem o comando → sugerir o comando antes de escrever
qualquer arquivo.

Conteúdo do recurso — descrição, seções, antipadrão de referência que não sobrevive à
publicação — segue `builder-resource-standards`, consultada ao escrever ou revisar o
corpo da skill.

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

## Recursos Instalados

## Restrições

**Segurança**
- Nunca commitar variáveis de ambiente (`.env*` sempre no `.gitignore`)
- Chaves de API nunca hardcoded no código

**Git**
- PRs para `main` exigem revisão manual
- Nunca fazer force push em `main`
```

As restrições são só o que vale para qualquer projeto. Havia um bloco por tipo, e a regra de migration
que vivia no de Development saía errada num projeto de Branding — restrição falsa no `CLAUDE.md`
ensina a ignorar as verdadeiras. Volta quando a personalização por tipo existir, que é o lugar dela.

#### Fragmentos padrão

Anexar ao final do arquivo, nesta ordem, o conteúdo de cada um destes, lido de
`${CLAUDE_PLUGIN_ROOT}/templates/claude-md/`:

| # | Arquivo | Seção que produz |
|---|---|---|
| 1 | `1-idioma-e-nomenclatura.md` | Idioma e Nomenclatura |

Copiar cada arquivo como está, sem reescrever e sem acrescentar separador: o `---` que separa as
seções já abre cada um deles.

O que resta vale para qualquer projeto, e por isso não depende do tipo escolhido no Passo 3. Vive
fora deste arquivo porque é conteúdo do artefato, não lógica do comando — e porque a variação por
tipo, quando existir, será uma lista de arquivos por tipo, não blocos alternativos aqui dentro.

### 5.3 — Gerar `.claude/rules/frontmatter.md`

Já existir → manter sem sobrescrever. O Passo 1 encerra o comando quando há `CLAUDE.md`, então o
caso que sobra é o projeto que tem regras sem `CLAUDE.md` — configurado à mão, e justamente o que não
se deve atropelar.

Gerar com a ferramenta Write, literalmente como abaixo. A norma de frontmatter não vive no `CLAUDE.md`: é procedimento de um domínio específico, e como regra escopada por `paths` só entra em contexto quando o Claude toca um recurso — em vez de custar contexto em toda sessão.

O bloco `paths` no topo **é** frontmatter, e aqui é lido: `.claude/rules/` é um dos dois lugares onde o Claude Code interpreta YAML no topo do arquivo.

````markdown
---
paths:
  - ".claude/**/*.md"
---

# Frontmatter de recurso

Recurso do AmFlow é markdown com manifesto no topo. Esta regra fixa o que não muda; a forma exata de
cada campo é aplicada por `/amflow-builder:build`, que carrega o template e a norma da versão
instalada do plugin.

## Não escrever à mão

Recurso novo — skill, agent, command, hook, module — se cria por `/amflow-builder:build`. Frontmatter
escrito à mão nasce fora da norma, e o Hub recusa submissão com `metadata` incompleto. Quando o
comando não estiver disponível, abrir um recurso do mesmo tipo já existente no projeto e seguir a
forma dele — nunca inventar campo.

## Skill

O `SKILL.md` segue a [especificação Agent Skills](https://agentskills.io/specification), e **não** a
forma dos outros tipos. Três regras estruturais:

1. **Só o `SKILL.md` tem frontmatter.** Arquivo em `scripts/`, `references/`, `assets/` ou
   `templates/` não tem. A norma alcança o arquivo, não a pasta.
2. **O topo aceita só os campos da spec e as extensões do Claude Code.** Campo em valor default não
   se escreve — omite-se.
3. **Dado do AmFlow vive em `metadata`, nunca no topo**, com prefixo `amflow-` em kebab-case e
   **valor sempre string** — a spec define `metadata` como mapa de string para string, e valor que
   não seja string é descartado.

A única chave com ponto é `amflow.module.<nome>`, registro de módulo instalado, escrito pelo
`/amflow-builder:install-module`. Não uniformizar com o resto.

## Os outros tipos

Agent, command e hook usam frontmatter YAML comum, com identidade (`name`, `type`, `description`,
`tags`), histórico (`author`, `version`, `status`, datas) e sistema (`scope`, `dependencies`). A
seção `hub` — `hub_id`, `source`, `price` — é preenchida por `/amflow-builder:publish` e
`/amflow-builder:publish-status`, nunca à mão.

## O que não é frontmatter

- **`CLAUDE.md`** — o Claude Code não interpreta YAML no topo dele.
- **Módulo** — o manifesto é o `module.json` ao lado do `MODULE.md`.
- **Arquivo interno de skill** — ver regra 1 acima.
````

### 5.4 — Gerar as regras de `templates/rules/`

Para cada arquivo `.md` em `${CLAUDE_PLUGIN_ROOT}/templates/rules/`, copiar o conteúdo verbatim
para `.claude/rules/<mesmo-nome>` com a ferramenta Write. Sem reescrever.

Já existir → manter sem sobrescrever, pelo mesmo motivo do 5.3: o caso que sobra é o projeto com
regras sem `CLAUDE.md`, configurado à mão.

Hoje são `execution-protocol.md`, `grounding-and-verification.md`, `tools.md` e `voice-and-language.md`.
Diferente do 5.3, nenhuma tem bloco `paths`: são conduta permanente, não procedimento de um domínio.
Sem `paths`, entram em contexto em toda sessão — que é o que se quer. Regra nova adicionada a
`templates/rules/` entra por aqui sem novo passo.

### 5.5 — Criar `settings.json`

Criar `<pasta>/.claude/settings.json` com conteúdo `{}`.

Já existir → manter sem sobrescrever.

## Pós-execução

Exibir ao usuário:

```
[ok] Projeto '<nome-projeto>' configurado em <pasta>

Criados:
  .claude/CLAUDE.md
  .claude/rules/execution-protocol.md
  .claude/rules/frontmatter.md
  .claude/rules/grounding-and-verification.md
  .claude/rules/tools.md
  .claude/rules/voice-and-language.md
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

- Nunca criar `.claude/CLAUDE.md` se já existir.
- Nunca sobrescrever `.claude/settings.json` nem nenhum arquivo já existente em `.claude/rules/`.
- O `CLAUDE.md` gerado não tem frontmatter.

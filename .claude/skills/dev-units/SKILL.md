---
# ── claude code — campos nativos ──────────────────────────────────────────────
name: dev-units
description: |
  Executa a norma de Unidades de Desenvolvimento do AmFlow em três modos — revisa um plano, deriva a estrutura e as unidades de um plano aprovado, ou implementa uma unidade em cold-start. Delega todo determinismo aos scripts em `scripts/`; o julgamento fica com a skill.

  Use when o usuário pede para revisar, derivar ou implementar algo do modelo de dev-units — sempre com o modo explícito no pedido.

  <example>
  Context: plano novo escrito no _inbox, ainda não aprovado
  user: "revise o plano docs/plan/_inbox/catalogo.md"
  commentary: modo review — os seis checks, isolando o que o script cobre (concorrência, fontes citadas) do que exige julgamento
  </example>

  <example>
  Context: plano aprovado, ainda sem estrutura nem unidades
  user: "derive o plano docs/plan/_inbox/catalogo.md"
  commentary: modo derive — cria a estrutura do alvo, move o plano do _inbox, gera um arquivo por unidade e projeta o backlog
  </example>

  <example>
  Context: unidade já derivada, pronta para execução
  user: "implemente a unidade 0002-11"
  commentary: modo implement — executa em cold-start, com gate de entrada (critério de aceite e teste declarados) e gate de saída (teste precisa passar antes de marcar verified)
  </example>

disable-model-invocation: false
user-invocable: true

allowed-tools: "Read Write Edit Bash Glob Grep"

argument-hint: "<review|derive|implement> <caminho>"
arguments: [mode, target]

model: ""
effort: ""
context: ""
shell: bash

# ── amflow — rastreabilidade ───────────────────────────────────────────────────
type: skill
project: AmFlow
author: Bortoli
created: 2026-07-25
status: draft
version: 1.0.0
updated: ""
scope: project
auto_load: false
tags: [dev-units, builder, skill, plano, unidade, cold-start]
dependencies: []

hub_id: ""
source: local
---

# dev-units

Executa a norma `docs/plan/system/modelo-dev-units.md` — a skill que substitui a `plan-dev-units` e opera os três modos que a norma define. Todo determinismo (gates, contagem, projeção de estado) fica nos scripts em `scripts/`; a skill cuida do que exige julgamento.

## O que faz

Revisa um plano antes da aprovação, deriva a estrutura e as unidades de um plano aprovado, ou implementa uma unidade específica em cold-start — conforme o modo recebido.

## Quando usar

- Para revisar um plano em `docs/plan/_inbox/` antes da aprovação
- Para derivar a estrutura e as unidades de um plano já aprovado
- Para implementar uma unidade já derivada

## Argumentos

- `$mode` — `review` | `derive` | `implement`
- `$target` — caminho do plano (`review`, `derive`) ou identificador da unidade (`implement`)

## Modo

O primeiro argumento da invocação é o modo — nunca inferido a partir do texto livre:

| Modo | Alvo | O que faz |
|---|---|---|
| `review` | plano | Os seis checks — parte por script, parte por julgamento |
| `derive` | plano aprovado | Cria a estrutura, move o plano do `_inbox`, gera as unidades, projeta o backlog |
| `implement` | unidade | Executa em cold-start, com gate de entrada e de saída |

Inferir o modo devolveria ao sistema a variância que o modelo existe para remover — um `derive` disparado quando se queria `review` cria estrutura e move arquivos.

**Sem modo, ou modo fora dos três:** recusar e listar as opções, sem escolher por conta própria.

> Modo ausente ou desconhecido. Use um dos três: `review <plano>`, `derive <plano>`, `implement <unidade>`.

## Fronteira skill / script

| Responsabilidade | Onde vive |
|---|---|
| Detectar modo, validar gates, medir lote, rodar teste, projetar estado, validar nome e colisão | Script — `scripts/` |
| Pesquisar, sintetizar, revisar com julgamento, decidir a fatia, escrever código, sugerir nomes | Esta skill |

Detalhe completo: norma, seções *Fronteira skill / script* e *Modo `review` — os seis checks*.

## Modelo

A skill herda o modelo de quem a invoca — a troca por modo não é declarável aqui (norma, decisão 18). `review` e `derive` pedem julgamento denso; `implement` roda por padrão em Sonnet, com override do usuário conforme o escopo. A escolha é operacional, feita antes de invocar — preencher `model:` daria falsa impressão de troca automática que a skill não faz.

## Instruções

### `review <plano>`

Os seis checks são os da norma (*Modo `review` — os seis checks*) — esta seção descreve só o **como**, para não duplicar o que já está lá (regra anti-drift, norma, seção *Camada normativa*).

1. **Determinístico, roda primeiro:**
   - **Nome** — `nomenclatura.validar_nome` sobre o stem do arquivo (`_inbox/<nome>.md` → `nome`).
   - **Concorrência** — lê `core`/`module` do frontmatter do plano; varre a região `planos` de `_planos.md` (mesmo acesso de `numeracao.py`, via `regioes.ler_regiao`) por uma linha `em desenvolvimento` no mesmo core **ou** módulo (norma, *Avaliação de escopo*). Encontrada, a linha inteira é a evidência citada no achado.
   - **Fontes citadas** — cada link relativo do corpo do plano resolve em disco.
   - Plano sem `core` no frontmatter: achado bloqueante — a concorrência fica registrada como não verificável, a revisão **não aborta**.
2. **Independência** — audita a seção `## Independência` do plano contra o teste da norma ("A e B passam isolados?"). Seção ausente é achado bloqueante, não silêncio.
3. **Tamanho como contexto** — unidades previstas, cores e módulos tocados, lidos da seção `## Escopo`. Relatar, nunca reprovar (decisão 26).
4. **Julgamento restante** — erros conceituais, erros de arquitetura, adequação das fontes ao escopo.
5. **Lacunas** — cada uma nova entra como `L-XX`, sem tentar resolvê-la.
6. **Relatório** — uma linha por achado: check, veredito (`bloqueante` | `aviso`) e origem (`comando` | `julgamento`). Sinalizar divisão não é reprovar — se o humano decide não dividir, o porquê fica registrado no plano, não neste relatório. Encerra sem aprovar — quem aprova é o humano.

Composição via `python3` (mesmo import dos testes, `sys.path` até `scripts/`): `.claude/skills/dev-units/scripts/nomenclatura.py` e `.claude/skills/dev-units/scripts/numeracao.py`.

### `derive <plano>`

A Sequência é a da norma (*Fluxo completo*, etapas 4 a 7) — esta seção descreve só o **como**, para não duplicar o que já está lá.

1. **Aprovar** — `scaffold.aprovar(plano)` valida `core`, atribui o número do plano, valida o nome, move o arquivo do `_inbox` (compondo `move-md.py`) e registra a linha em `_planos.md`. Qualquer validação que falhar impede toda escrita.
2. **Ler o escopo** — a tabela `## Escopo` do plano já movido: uma linha por unidade prevista, com número e responsabilidade.
3. **Decidir a fatia** — para cada unidade, o contrato, a sequência e os arquivos que ela toca. **É aqui que está o julgamento**, e por isso o modo pede Opus, nunca Sonnet.
4. **Numerar e escrever** — `numeracao.proxima_unidade(dir_plano)` dá o próximo `nn`; cada arquivo carrega todos os blocos do corpo (norma, *Formato do arquivo de unidade*) e declara `test:` mesmo antes de o arquivo existir (decisão 15).
5. **Lint antes de seguir** — `lint_unidade.lint(arquivo)` em cada unidade recém-escrita; qualquer problema apontado é corrigido ali, antes de passar para a próxima.
6. **Projetar o backlog** — `backlog.projetar(dir_plano)`, que atualiza também a situação da linha em `_planos.md`.
7. **Registrar e relatar** — decisões tomadas durante a derivação vão para uma seção própria do plano, nunca para a norma; lacunas novas entram como `L-XX`, sem tentar resolvê-las; o que ficou pendente é reportado ao humano.

> **O lint roda antes de entregar** (passo 5). Sem isso, o `derive` produz unidades que o gate de entrada do `implement` recusa depois, e o retrabalho só aparece na próxima sessão.

Composição via `python3` (mesmo import dos testes, `sys.path` até `scripts/`): `.claude/skills/dev-units/scripts/scaffold.py`, `.claude/skills/dev-units/scripts/numeracao.py`, `.claude/skills/dev-units/scripts/lint_unidade.py` e `.claude/skills/dev-units/scripts/backlog.py`.

### `implement <unidade>`

Os dois gates são os da norma (*Os dois gates*, decisão 15) — esta seção descreve só o **como**, para não duplicar o que já está lá.

1. **Gate de entrada** — `lint_unidade.lint(unidade)`; qualquer problema recusa e encerra sem escrever nada, e a correção volta ao `derive`.
2. **Ler a unidade inteira** — contrato, sequência, arquivos, normas referenciadas e critério de aceite.
3. **Abrir as normas citadas** na tabela — são referências, o conteúdo delas não está copiado na unidade.
4. **Escrever o teste declarado**, cobrindo o critério de aceite — teste e código são entregáveis da mesma unidade (decisão 15); exigir teste preexistente tornaria impossível começar unidade nova.
5. **Escrever o código** que faz o teste passar, tocando apenas os arquivos que a unidade declara.
6. **Gate de saída** — `verificacao.verificar(unidade)`; teste falhando, a unidade não transiciona para `verified`.
7. **Projetar o backlog** do plano com `backlog.projetar(dir_plano)`.
8. **Relatar** o que foi feito — se algo da unidade estava insuficiente, dizer o quê; a correção é da unidade, nunca do executor.

> **Se o executor precisou perguntar, a unidade falhou.** O teste é empírico e barato, e a
> insuficiência volta para quem deriva — nunca é resolvida por conta própria em execução.

> **O executor não commita.** O modo entrega arquivos e relatório; versionar é de quem orquestra, que
> revisa a entrega antes de registrá-la.

Composição via `python3` (mesmo import dos testes, `sys.path` até `scripts/`): `.claude/skills/dev-units/scripts/lint_unidade.py`, `.claude/skills/dev-units/scripts/verificacao.py` e `.claude/skills/dev-units/scripts/backlog.py`.

## Referências

- Norma: `docs/plan/system/modelo-dev-units.md`
- Plano desta skill: `docs/plan/builder/0002-dev-units/0002-dev-units.md`
- Skill substituída: `.claude/skills/plan-dev-units/SKILL.md` (removida pela unidade 0002-15)

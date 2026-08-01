# AmFlowPlugins — Instruções do Projeto

## Visão geral

Catálogo público dos plugins do AmFlow para o Claude Code — a fonte que `/plugin marketplace add`
lê. O desenvolvimento do produto AmFlow acontece em outro repositório, privado. Aqui vive só o
necessário para instalar e para trabalhar nos dois plugins: `amflow-worker` e `amflow-builder`.

## Mapa do repositório

| Caminho | O que vive aqui |
|---|---|
| `.claude-plugin/marketplace.json` | Catálogo — declara as duas entradas de plugin |
| `plugins/worker/` | Plugin `amflow-worker` |
| `plugins/builder/` | Plugin `amflow-builder` |
| `.claude/` | Workspace deste repositório — instruções e a skill `dev-units` |
| `docs/plan/` | Planos e unidades de desenvolvimento deste repositório |
| `scripts/test-python.sh` | Runner dos testes Python daqui |

## Formato do `marketplace.json`

Declara `name`, `description`, `owner` e a lista `plugins` — cada entrada com `name`, `source`
(caminho relativo, ex.: `./plugins/worker`) e `description`. `source` é sempre um caminho dentro
deste repositório, nunca uma URL externa.

## Invariantes

- Os identificadores instalados não mudam: `amflow-worker@amflow` e `amflow-builder@amflow`.
  Renomear qualquer um dos dois — plugin ou marketplace — deixa quem já instalou com uma entrada
  órfã.
- `version` mora em cada `plugin.json` do respectivo plugin. Nunca é derivada da fonte (hash de
  commit, data) — é o que o Claude Code exibe como versão instalada.
- Este repositório é público. Nenhum arquivo aqui cita infraestrutura, documentação interna ou
  identificadores do repositório de desenvolvimento do AmFlow.

## Trabalho novo

Feature, correção ou plano novo segue o mesmo modelo do repositório de desenvolvimento: nasce em
`docs/plan/_inbox/`, passa por revisão, aprovação humana, derivação em unidades e implementação uma
unidade por vez. Invocar a skill `dev-units`; norma completa em
[`docs/plan/system/modelo-dev-units.md`](../docs/plan/system/modelo-dev-units.md).

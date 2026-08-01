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

### Antes de editar a skill `dev-units` daqui — pare

Ela é **cópia**. A mesma skill existe no repositório de desenvolvimento do AmFlow, e as duas foram
idênticas no dia em que esta chegou. Não há nada que avise quando deixarem de ser: nenhum teste, nenhum
guard, nenhum CI compara as duas.

Editar só um dos lados é como o projeto já falhou antes — foi o argumento que aposentou o canal npm:
manter dois artefatos que deveriam andar juntos produz deriva, e a deriva só aparece quando alguém
depende da metade errada.

**Se você chegou aqui para editar a skill, a edição não é o próximo passo — a decisão é.** Escolher
entre fonte única (submódulo git, ou instalar a skill publicada pelo próprio AmFlow) e assumir as duas
cópias com um mecanismo que force a paridade. Só depois disso, editar.

A skill copiada vem **sem a suíte de testes** de propósito: os testes dela são de integração contra o
conteúdo do AmFlow — copiam arquivos de lá, lintam unidades que só existem lá — e nunca passariam
aqui. Este repositório **consome** a skill; quem a desenvolve é o AmFlow.

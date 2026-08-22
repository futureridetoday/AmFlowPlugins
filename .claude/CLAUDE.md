# AmFlowPlugins — Instruções do Projeto

## Visão geral

Catálogo público dos plugins do AmFlow para o Claude Code — a fonte que `/plugin marketplace add`
lê. Aqui vive só o necessário para publicar, instalar e atualizar o marketplace e os dois plugins:
`amflow-worker` e `amflow-builder`.

## Mapa do repositório

| Caminho | O que vive aqui |
|---|---|
| `.claude-plugin/marketplace.json` | Catálogo — declara as duas entradas de plugin |
| `plugins/worker/` | Plugin `amflow-worker` |
| `plugins/builder/` | Plugin `amflow-builder` |
| `.github/workflows/plugins.yml` | Guard de publicação — valida manifestos e frontmatter |
| `scripts/check-surface.py` | Guard de publicação — separação de superfícies MCP |

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

## Este repositório não é onde se desenvolve

É o pacote, não a oficina. Plano, correção, melhoria e evolução dos plugins acontecem no repositório
de desenvolvimento do AmFlow, privado, e chegam aqui já decididos — como conteúdo de `plugins/` ou
como entrada no catálogo.

Isso vale inclusive para uma correção que parece pequena. Editar direto aqui produz uma versão que
não existe do outro lado, e nada neste repositório avisa quando os dois divergem: não há teste, não
há guard de paridade, não há CI que compare. Foi o argumento que aposentou o canal npm — manter dois
artefatos que deveriam andar juntos produz deriva, e a deriva só aparece quando alguém depende da
metade errada.

Os dois guards que rodam aqui — `plugins.yml` e `check-surface.py` — validam o que está prestes a ser
publicado. Não substituem a revisão que acontece do outro lado.

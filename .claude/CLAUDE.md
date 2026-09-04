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
| `plugins/builder/templates/claude-md/` | O fragmento de conduta — fonte da seção deste arquivo |
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
- Nada que o plugin distribui pode apontar para o repositório de desenvolvimento. Ponteiro que
  resolve aqui e morre no destino é o defeito mais recorrente deste projeto — ocorreu na unidade
  0003-04 do Worker, foi corrigido, e voltou em quatorze ocorrências no Builder. Quando o ponteiro
  carrega informação, inlinar a informação; quando o próprio recurso já a cobre, cortar.

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

### Como exceder a regra

A regra é excedível, e o caminho é declarado para não virar pergunta repetida a cada sessão:

1. **O override é explícito e do mantenedor.** Não se infere de "pode corrigir" nem de urgência.
   Perguntar uma vez, com a consequência nomeada; resposta afirmativa vale para o trabalho em curso.
2. **Perguntar uma vez, não a cada arquivo.** Override concedido cobre a sessão. Repetir a pergunta
   é atrito, não zelo.
3. **O que foi editado aqui precisa ser replicado do outro lado.** Ao encerrar o trabalho, listar os
   arquivos tocados — é o único registro de divergência que existe.

## Git

- **Commit direto em `main`.** Este repositório não usa branch de trabalho.
- **Nunca criar branch sem permissão explícita.**
- Nunca fazer force push em `main`.
- Nunca fazer push sem pedido — commit e push são atos separados aqui.

## Frontmatter dos recursos do plugin

Os recursos dentro de `plugins/` têm frontmatter, e **a forma difere por tipo**:

- **`skill`** — segue a especificação Agent Skills. No topo vivem só `name`, `description`,
  `license` e os campos condicionais da spec. Todo dado do AmFlow vive em `metadata`, com prefixo
  `amflow-` e valor sempre string. **Não existe `type`, `version`, `status` nem `created` no topo de
  uma skill.**
- **`agent`, `command`, `hook`** — frontmatter YAML comum, com `name`, `type`, `description`,
  `version`, `status` e o resto no topo.

Confundir as duas formas é o defeito que reprovava toda skill gerada pelo próprio Builder. A tabela
de referência por tipo está em [`plugins/builder/agents/reviewer/reviewer.md`](../plugins/builder/agents/reviewer/reviewer.md),
passo 4.

O `plugins.yml` **não valida a forma** — confere só que a primeira linha do arquivo é `---`. Ausência
de erro no CI não é evidência de frontmatter correto.

## Este arquivo não tem frontmatter

E não é esquecimento. O Claude Code entrega o `CLAUDE.md` como mensagem de usuário e não interpreta
bloco YAML no topo — frontmatter aqui é texto que consome contexto em toda sessão sem ser lido por
nada. É a mesma regra que o `/amflow-builder:new-project` aplica ao gerar o `CLAUDE.md` de um projeto
novo.

## Sobre a seção abaixo

É cópia literal do fragmento em `plugins/builder/templates/claude-md/`, o mesmo que o
`/amflow-builder:new-project` injeta no `CLAUDE.md` de todo projeto criado. Fica inline porque regra
de conduta precisa estar no contexto, não a um `Read` de distância.

Alterou o fragmento, atualizar aqui — e vice-versa. Diferente de tudo mais neste repositório, os dois
lados desta cópia moram aqui, então a divergência é verificável por diff.

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

# status

Versão 1.0.0

## O que é

Um painel de status para os recursos que o Creator está construindo: mostra o que está em andamento,
pausado, bloqueado, pronto para publicar, em revisão pelo Hub, com ajustes pedidos, recusado ou
publicado — e deixa mudar esse estado sem abrir o arquivo à mão.

## Problema que resolve

Antes desta skill, o status de um recurso vivia em três domínios diferentes por tipo, em dois lugares
diferentes do frontmatter, e ninguém lia o valor para decidir nada. Saber o que falta terminar num
projeto com dezenas de recursos exigia abrir cada arquivo; mudar o status era editar o frontmatter à
mão, sem verificação nenhuma de que o valor fazia sentido.

## Como funciona

Um único campo, `metadata.amflow-status`, com nove valores possíveis — cinco que o Creator declara,
quatro que a publicação grava a partir do retorno do Hub. A skill nunca decide sozinha: ela interpreta
o pedido do Creator — listar tudo, filtrar por um estado, ou mudar o estado de um recurso — e chama o
`status.py`, que varre o projeto, valida o valor contra o domínio e grava preservando o resto do
arquivo.

Não há chamada de rede. O estado do Hub que aparece na lista é o que a última execução do
`/amflow-builder:publish-status` gravou — a skill mostra isso junto do resultado, nunca finge saber
mais do que o arquivo diz.

A lista sai como tabela, com o nome de cada recurso em link — clicar abre o arquivo direto —, e uma
coluna com a data da última edição. A ordem agrupa por tipo de recurso e, dentro do tipo, pelo que
precisa de ação primeiro, com o mais recente no topo.

## Como usar

Por linguagem natural, sem comando fixo — a descrição da skill é a própria superfície de ativação:

> "o que eu tenho pendente para terminar neste projeto?"

> "marca a skill deep-research como bloqueada, esperando a API de licenças"

> "quais recursos estão prontos para publicar?"

> "retoma o command publish-status"

## Exemplos de uso

**Retomando um projeto depois de semanas.** O Creator pergunta o que está pendente. A skill devolve
uma tabela agrupada por tipo de recurso e, dentro de cada tipo, pelo que precisa de ação primeiro —
o que o Hub pediu ajuste, o que está pronto para publicar, o que está em andamento —, mais recente
no topo; ele decide por onde continuar clicando direto no link de cada um.

**Pausando por dependência externa.** Um agent depende de uma API que ainda não existe. O Creator
pede para marcá-lo como bloqueado, com o motivo; a skill exige o motivo antes de gravar, porque
bloqueado sem motivo não se distingue de pausado.

**Antes de publicar.** O Creator pergunta quais recursos estão prontos. A skill filtra por `review` e
devolve só esses — sem precisar abrir cada frontmatter para conferir.

## Fundamentação

O campo, o domínio dos nove valores, a chave do motivo de bloqueio e a ordem de exibição vêm de
`docs/plan/builder/0014-unify-status-field/index.md`, no repositório onde o Builder é desenvolvido —
documento privado, nunca citado ao Creator. O determinismo inteiro mora em `status.py`; esta skill
não redeclara nada disso em prosa.

## Base de conhecimento

Nenhuma embutida. Tudo o que a skill mostra vem da varredura que o `status.py` faz no momento do
pedido, sobre os arquivos reais do projeto.

## Limites

- **Não consulta o Hub.** O estado de publicação que aparece é o da última sincronização por
  `/amflow-builder:publish-status` — pode estar desatualizado, e a skill avisa isso no rodapé
- **Não publica nem revisa.** Marcar como `review` é o Creator dizendo que terminou; publicar de
  fato é `/amflow-builder:publish`
- **Não grava os quatro valores do Hub.** `pending_review`, `changes_requested`, `rejected` e
  `published` só entram pelos comandos de publicação
- **Cobre só skill, agent, command, hook e módulo** — os cinco tipos que o Builder cria

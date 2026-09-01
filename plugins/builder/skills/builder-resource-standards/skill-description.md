# builder-resource-standards

Versão 1.0.0

## O que é

A referência de julgamento consultada enquanto uma skill do AmFlow ganha conteúdo — depois que
`build-resource` já criou a estrutura. Explica por que o frontmatter exige cada campo, como
escolher o arquétipo certo e o peso de cada seção, e os dois antipadrões de autoria que o
verificador de frontmatter não pega.

## Problema que resolve

A estrutura de uma skill nasce pronta, mas o conteúdo não. O que separa uma `description` que ativa
no caso certo de uma que ativa demais, uma seção principal de uma decorativa, um antipadrão que se
repete de um acidente isolado — isso não estava em lugar nenhum que uma skill recém-criada pudesse
ler. A norma existia, mas em três lugares, e nenhum alcançava o projeto onde a skill estava sendo
escrita.

## Como funciona

Não tem processo — é consultada, não executada. O corpo traz os dois antipadrões de autoria mais
recorrentes; duas referências ao lado cobrem o resto: por que o frontmatter é como é, e como
escolher entre os quatro arquétipos de skill e seus cinco padrões de instrução.

## Como usar

Automática, pela `description`, no momento de escrever ou revisar o corpo de uma skill — não para
criar a estrutura inicial, isso é `build-resource`, nem para validar formato, isso é o `check.py`
vendorizado ou o agent `reviewer`.

## Exemplos de uso

**Escolhendo seção.** Ao decidir se uma skill de contexto de projeto precisa de uma `## Instruções`
extensa, a referência de arquétipos mostra que essa seção pesa pouco nesse arquétipo — o peso está
em `## Gotchas`.

**Evitando o antipadrão que originou esta skill.** Ao escrever um ponteiro para um arquivo de
documentação, checar antes se ele viaja com a skill publicada — se não viaja, o ponteiro quebra no
destino, nunca no repositório de origem, onde ninguém o veria quebrado.

## Fundamentação

Nasceu de um defeito medido: o `CLAUDE.md` gerado por `new-project` dizia onde cada recurso mora e
qual comando o cria, mas nada sobre o que faz uma skill boa. A instrução existia — em três lugares —
e nenhum alcançava o projeto onde ela fazia falta. Norma de julgamento não pode ser copiada para
dentro do projeto criado, porque muda com o plugin e congelaria desatualizada — por isso vive aqui,
como skill, não como texto herdado no `CLAUDE.md` gerado.

## Base de conhecimento

- Os quatro arquétipos de skill e o peso de seção de cada um
- Os cinco padrões de instrução (A–E)
- Por que o frontmatter do AmFlow vive em `metadata`, sob prefixo `amflow-`
- Os dois antipadrões de autoria com recorrência documentada no histórico do projeto

## Limites

- **Cobre só `skill`.** `agent`, `hook` e `command` seguem sem esta camada de julgamento — a norma
  de frontmatter geral, fora desta skill, continua sendo o único guia para os três.
- **Não valida.** Quem decide se o frontmatter está sintaticamente correto é o `check.py`
  vendorizado; esta skill explica o porquê, nunca substitui o veredito dele.
- **Não cria estrutura.** Isso é `build-resource`.

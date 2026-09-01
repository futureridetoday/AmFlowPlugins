---
name: builder-resource-standards
description: Orienta a autoria do conteúdo de uma skill do AmFlow depois que a estrutura já existe — por que a norma de frontmatter exige cada campo, como escolher arquétipo e peso de seção, e os antipadrões de autoria que o verificador de frontmatter não pega. Use ao escrever ou revisar o corpo de uma skill; para criar a estrutura inicial, use build-resource.
license: Proprietary
metadata:
  amflow-version: "1.0.0"
  amflow-status: draft
  amflow-author: Bortoli
  amflow-author-id: 985920db-502d-4cb3-9ca1-c145719a9307
  amflow-updated: "2026-09-01"
  amflow-tags: authoring skill standards frontmatter antipattern
  amflow-dependencies: ""
---

# Builder Resource Standards

Referência de julgamento para quem está dando conteúdo a uma skill do AmFlow — não para quem está
criando a estrutura dela. Consultada durante a Fase 3+ do `build-resource`, ou sempre que uma skill
existente ganha ou revisa conteúdo.

## Quando usar

- Escrevendo a `description` de uma skill e decidindo se ela ativa no caso certo, sem ativar demais
- Decidindo que seções o `SKILL.md` precisa, e quanto peso cada uma merece
- Revisando um `SKILL.md` já escrito atrás de referência que não vai sobreviver à publicação

## Não usar quando

- A estrutura ainda não existe — isso é `build-resource`
- A dúvida é se o frontmatter está sintaticamente correto — isso é o `check.py` vendorizado
  (`${CLAUDE_PLUGIN_ROOT}/scripts/check.py`) ou o agent `reviewer`, nunca julgamento

## Gotchas

**Referência que não sobrevive ao destino.** Um ponteiro dentro do `SKILL.md` para um arquivo que só
existe do lado de quem escreveu a skill — norma interna, guia de preenchimento, documento de
sistema — resolve enquanto o autor edita e quebra no Hub, no bundle publicado e na cópia instalada.
Regra: ler o material de referência para decidir o conteúdo, nunca apontar para ele de dentro do
recurso que vai viajar sozinho.

**Colisão de nome entre domínios.** `amflow-source`, no frontmatter, diz de onde a skill veio no
Hub. `source`, campo próprio da API de skills, diz como ela chegou à conta do usuário — e responde
`"custom"` sem relação nenhuma com o outro. Nomes iguais, donos diferentes: não misturar o que uma
plataforma expõe com o que a norma do AmFlow define, só porque soam parecidos.

## Referências

| Arquivo | Cobre |
|---|---|
| [`references/frontmatter.md`](references/frontmatter.md) | Por que o frontmatter é como é — os três blocos, o prefixo `amflow-`, os dois erros que o verificador não avisa |
| [`references/arquetipos.md`](references/arquetipos.md) | Os quatro arquétipos de skill, peso de seção por arquétipo, os cinco padrões de instrução |

## Limites

Cobre autoria de **skill**. `agent`, `hook` e `command` não têm camada de julgamento equivalente
ainda — seguem só pela norma de frontmatter geral, fora desta skill.

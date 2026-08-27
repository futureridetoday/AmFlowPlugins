---
name: describe-resource
description: Responde perguntas sobre um recurso da autoria do próprio Creator — o que é, como usar, exemplos, em que se fundamenta e o que ele não faz — lendo o `[tipo]-description.md` do disco. Use when o Creator pergunta sobre uma skill, agent ou módulo do próprio projeto ("como usar a skill X?", "o que o agent Y faz?", "quais os limites do módulo Z?"), ou quando precisa saber se um recurso serve para uma tarefa antes de adotá-lo. Use esta skill EM VEZ DE ler o SKILL.md, o MODULE.md ou o .md do agent para responder: aqueles arquivos são instrução de execução, escritos para o agente seguir, e respondem como fazer; o documento de descrição é escrito para uma pessoa decidir, e responde o que é e quando cabe. Responder a partir do arquivo de instrução devolve procedimento onde se pediu explicação. Invocada também por /amflow-builder:describe
license: Proprietary
metadata:
  amflow-version: "1.0.0"
  amflow-status: draft
  amflow-author: Bortoli
  amflow-author-id: 2cfea9a3-e127-4fa1-ac7c-b422d31fb63e
  amflow-updated: "2026-08-27"
  amflow-tags: creator documentacao recurso skill agent module description
  amflow-dependencies: ""
---

# Describe Resource

Responde sobre um recurso **da autoria do Creator**, lendo o documento de descrição que vive na raiz da
pasta do recurso. É leitura de disco: sem rede, sem tool e sem autenticação.

## Quando usar

- O Creator pergunta o que um recurso do projeto faz, como usá-lo ou quais são seus limites
- Ele retoma um recurso escrito há semanas e não lembra do próprio desenho
- Precisa decidir se um recurso já existente serve para a tarefa, antes de criar outro

## Não usar quando

- A pergunta é sobre recurso de **terceiro**, do catálogo do Hub — aí a fonte é a página do recurso ou
  a tool `get_resource`, que devolve a mesma documentação do lado do servidor
- A pergunta é sobre **como o recurso foi implementado** por dentro. O documento explica o que é e
  quando cabe; o `SKILL.md`, o `<nome>.md` do agent e o `MODULE.md` é que dizem como executar
- O Creator quer **criar** um recurso — é o `/amflow-builder:build`

## Processo

1. **Identificar tipo e nome** a partir da pergunta. Quando o tipo não for dito, procurar nos três:

   ```bash
   ls -d .claude/skills/<nome> .claude/agents/<nome> .claude/modules/<nome> 2>/dev/null
   ```

   Nada encontrado → listar o que existe e perguntar qual é:

   ```bash
   ls .claude/skills .claude/agents .claude/modules 2>/dev/null
   ```

2. **Ler o documento**, no caminho derivado do tipo:

   | Tipo | Caminho |
   |---|---|
   | `skill` | `.claude/skills/<nome>/skill-description.md` |
   | `agent` | `.claude/agents/<nome>/agent-description.md` |
   | `module` | `.claude/modules/<nome>/module-description.md` |

3. **Responder a pergunta que foi feita**, não o documento inteiro. Cada pergunta tem sua seção:

   | O Creator pergunta | Seção |
   |---|---|
   | o que é · para que serve | `## O que é` e `## Problema que resolve` |
   | como usar · como invocar · como chamar | `## Como usar` |
   | tem exemplo · em que caso usar | `## Exemplos de uso` |
   | em que se baseia · qual o método | `## Fundamentação` |
   | o que ele carrega · que dados usa | `## Base de conhecimento` |
   | o que não faz · dá para usar em X | `## Limites` |
   | pergunta aberta, sem recorte | `## O que é` e `## Como usar`, e oferecer o resto |

   Responder com o conteúdo do documento, não com uma paráfrase inventada. Se a seção pedida estiver
   vazia ou ausente, dizer isso — em vez de preencher com suposição.

4. **Citar a versão** que o documento declara, quando a resposta depender dela. Documento é da versão
   que ele diz ser, não necessariamente da que está instalada.

## Quando o documento não existe

Três casos, com respostas diferentes:

| Situação | Resposta |
|---|---|
| Recurso existe, documento ausente | Dizer que o recurso não tem documento e **oferecer criá-lo** a partir do template do tipo, em `${CLAUDE_PLUGIN_ROOT}/templates/`. É obrigatório para publicar no Hub |
| Recurso é `command` ou `hook` | Esses tipos ainda não entraram na norma. Responder a partir do próprio arquivo do recurso, avisando que a resposta não vem de documento de descrição |
| Agent em arquivo solto (`.claude/agents/<nome>.md`, sem pasta) | Layout anterior à norma. Não há documento; oferecer converter para `.claude/agents/<nome>/<nome>.md` com o documento ao lado |

## Restrições

- **Nunca inventar conteúdo de seção.** Se o documento não responde, dizer que não responde. O valor
  desta skill é ser fiel ao que o Creator escreveu — uma resposta plausível e falsa é pior que "o
  documento não diz".
- **Não editar o recurso** ao responder. Criar ou corrigir o documento é ação à parte, e só depois de
  o Creator pedir.
- **Não usar isto para recurso de terceiro.** O documento no disco de um recurso instalado é a cópia
  da versão instalada; para o catálogo, a fonte é o Hub.

## Referência

A norma do documento — forma, seções e regras — vive no repositório AmFlow, em
`docs/plan/system/resource-description.md`.

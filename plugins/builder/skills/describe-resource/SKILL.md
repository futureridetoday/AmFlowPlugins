---
name: describe-resource
description: Responde perguntas sobre um recurso da autoria do próprio Creator — o que é, como usar, exemplos, em que se fundamenta e o que ele não faz — lendo o `[tipo]-description.md` do disco. Use when o Creator pergunta sobre uma skill, agent ou módulo do próprio projeto ("como usar a skill X?", "o que o agent Y faz?", "quais os limites do módulo Z?"), ou quando precisa saber se um recurso serve para uma tarefa antes de adotá-lo. Use esta skill EM VEZ DE ler o SKILL.md, o MODULE.md ou o .md do agent para responder: aqueles arquivos são instrução de execução, escritos para o agente seguir, e respondem como fazer; o documento de descrição é escrito para uma pessoa decidir, e responde o que é e quando cabe. Responder a partir do arquivo de instrução devolve procedimento onde se pediu explicação. Invocada também por /amflow-builder:describe
license: Proprietary
metadata:
  amflow-version: "1.1.0"
  amflow-status: draft
  amflow-author: Bortoli
  amflow-author-id: 985920db-502d-4cb3-9ca1-c145719a9307
  amflow-updated: "2026-09-19"
  amflow-tags: creator documentacao recurso skill agent module description
  amflow-dependencies: ""
---

# Describe Resource

Responde sobre um recurso **da autoria do Creator**, lendo o documento de descrição que vive na raiz da
pasta do recurso. É leitura de disco: sem rede e sem autenticação. Quem localiza o recurso é o
`status.py`, que já conhece as duas pastas onde ele pode estar.

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

1. **Resolver o projeto** — `$CLAUDE_PROJECT_DIR` quando definido; senão, o diretório de trabalho
   atual. É o `<projeto>` do comando abaixo.

2. **Listar os recursos**, nunca reimplementar a varredura:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" list <projeto>
   ```

   O script varre a pasta de desenvolvimento — `skills/`, `agents/` e `modules/`, na raiz do projeto — e
   `.claude/`, e devolve uma tabela `| Tipo | Nome | Local | Status | Atualizado | Rótulo |`. Ler a saída:

   | Saída | O que fazer |
   |---|---|
   | Código 0, com tabela | Seguir para o passo 3 |
   | Código 0, sem tabela | Dizer que o projeto não tem recurso do Creator, e encerrar |
   | Código 1 | Alguma linha começa com `ERRO` — um arquivo de recurso não parseou. Se o recurso pedido está na tabela, seguir e avisar em uma linha; se não está, dizer que ele pode estar entre esses arquivos |

   O rodapé que o `list` imprime depois da tabela não entra na resposta.

3. **Escolher a linha** a partir da pergunta:
   - Tipo dito → a linha `tipo`/`nome`. Tipo omitido → as linhas com o nome; havendo mais de um tipo,
     perguntar qual é.
   - Nenhuma linha → mostrar a tabela e perguntar qual recurso é. Nunca adivinhar.
   - O mesmo tipo e nome nos dois locais → vale o da pasta de desenvolvimento (`Local` sem o prefixo
     `.claude/`), e uma linha avisa que há cópia em `.claude/`. A pasta de desenvolvimento é a fonte;
     `.claude/` guarda o que está em uso.

4. **Ler o documento**, na pasta do `Local` — `skills/deep-research/SKILL.md` leva a
   `skills/deep-research/skill-description.md`:

   | Tipo | Documento |
   |---|---|
   | `skill` | `skill-description.md` |
   | `agent` | `agent-description.md` |
   | `module` | `module-description.md` |

5. **Responder a pergunta que foi feita**, não o documento inteiro. Cada pergunta tem sua seção:

   | O Creator pergunta | Seção |
   |---|---|
   | o que é · para que serve | `## O que é` e `## Problema que resolve` |
   | como funciona · o que acontece por dentro | `## Como funciona` |
   | como usar · como invocar · como chamar | `## Como usar` |
   | tem exemplo · em que caso usar | `## Exemplos de uso` |
   | em que se baseia | `## Fundamentação` |
   | o que ele carrega · que dados usa | `## Base de conhecimento` |
   | o que não faz · dá para usar em X | `## Limites` |
   | pergunta aberta, sem recorte | `## O que é` e `## Como usar`, e oferecer o resto |

   Responder com o conteúdo do documento, não com uma paráfrase inventada. Seção só com comentário
   HTML — o esqueleto que o `build` entrega — é seção vazia. Vazia ou ausente:
   - `Fundamentação` e `Base de conhecimento` são opcionais: dizer que o recurso não declara, não que o
     documento não diz. A Fundamentação traz só nomes — responder com os nomes, sem completar a
     explicação.
   - Nas demais, dizer que o documento não diz — em vez de preencher com suposição.

6. **Citar o que a resposta pede:**
   - A versão que o documento declara, quando a resposta depender dela. Documento é da versão que ele diz
     ser; se a linha `Versão` difere da versão do manifesto — `metadata.amflow-version` no `SKILL.md`,
     `version` no `<nome>.md` do agent e no `module.json` —, avisar: recurso em andamento deriva sem
     ninguém conferir.
   - O `Rótulo` do status, da tabela — "Em andamento", "Publicado". Status `deprecated` ou `blocked`
     pede aviso explícito, porque quem pergunta está prestes a adotar o recurso.

## Quando o documento não existe

Três casos, com respostas diferentes:

| Situação | Resposta |
|---|---|
| Recurso existe, documento ausente | Dizer que o recurso não tem documento e **oferecer criá-lo** a partir do template do tipo: `${CLAUDE_PLUGIN_ROOT}/templates/skills/skill/skill-description.md`, `${CLAUDE_PLUGIN_ROOT}/templates/agents/agent-description.md` ou `${CLAUDE_PLUGIN_ROOT}/templates/modules/default/module-description.md`. É obrigatório para publicar skill e agent no Hub; o módulo não passa pelo gate, mas carrega o documento pelo mesmo motivo |
| Recurso é `command` ou `hook` | Esses tipos ainda não entraram na norma. O `Local` aponta o próprio arquivo: responder a partir dele, avisando que a resposta não vem de documento de descrição |
| Agent em arquivo solto (`Local` = `agents/<nome>.md`, sem pasta) | Layout anterior à norma. Não há documento; oferecer converter para `agents/<nome>/<nome>.md` com o documento ao lado |

## Restrições

- **Nunca inventar conteúdo de seção.** Se o documento não responde, dizer que não responde. O valor
  desta skill é ser fiel ao que o Creator escreveu — uma resposta plausível e falsa é pior que "o
  documento não diz".
- **Não editar o recurso** ao responder. Criar ou corrigir o documento é ação à parte, e só depois de
  o Creator pedir.

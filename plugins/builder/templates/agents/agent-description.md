<!-- Destino: agents/<nome>/agent-description.md — raiz da pasta do agent, ao lado do <nome>.md.
     Norma: docs/plan/system/resource-description.md (repositório AmFlow).

     Agent é diretório, como skill: agents/<nome>/<nome>.md + agent-description.md.
     A descoberta do Claude Code é recursiva e a identidade vem do campo `name` do frontmatter,
     então a pasta não muda como o agent é invocado — exceto em agent distribuído dentro de um
     plugin, onde o caminho compõe o identificador e a subpasta acrescenta um segmento.

     Markdown puro: sem frontmatter, sem YAML, sem JSON. Os metadados já vivem no <nome>.md.

     O leitor é quem NÃO conhece o agent. O <nome>.md é a instrução que o agent segue; este
     arquivo explica o que ele é e quando vale delegar a ele.

     Títulos exatos e nesta ordem — o gate compara literal. Fundamentação e Base de conhecimento
     são opcionais; as outras seis não. Subtítulos ### são livres por dentro. -->

# agent-name

<!-- O valor exato do campo `name` do frontmatter. É identificador, não título editorial. -->

Versão 1.0.0

<!-- Linha isolada, na forma `Versão X.Y.Z`. Precisa bater com o `version` do frontmatter —
     ao subir a versão do agent, subir aqui também. -->

## O que é

<!-- Uma frase, para quem não conhece o domínio. O papel que o agent cumpre, dito como se
     descreve uma função a alguém que vai contratá-la. -->

## Problema que resolve

<!-- Por que delegar isto a um agent em vez de fazer na conversa principal. Normalmente é uma
     de três razões: o trabalho é longo e polui o contexto, exige um ponto de vista
     independente, ou precisa rodar em paralelo com outros. Diga qual é a sua. -->

## Como funciona

<!-- A autonomia que ele tem: o que decide sozinho, o que devolve para o humano decidir, e onde
     está a linha entre os dois. Depois, o que ele recebe ao ser invocado e o que devolve ao
     terminar — um agent entrega uma resposta, não uma conversa.
     Mencione as ferramentas a que tem acesso quando isso mudar o que ele consegue fazer. -->

## Como usar

<!-- Quando delegar a ele em vez de resolver inline, e como invocá-lo — pelo nome, ou pela
     descrição que o Claude usa para escolher sozinho.
     Diga também o que preparar antes: um agent que recebe contexto incompleto devolve
     trabalho incompleto. -->

## Exemplos de uso

<!-- Dois a quatro cenários concretos. Cada um: a situação, o que foi delegado, o que voltou.
     Inclua ao menos um caso em que ele escala para o humano em vez de decidir — é o que mostra
     onde fica a fronteira da autonomia. -->

## Fundamentação

<!-- Opcional. O método ou o critério que sustenta o julgamento do agent — a checklist que ele
     aplica, a norma que segue, o padrão contra o qual avalia. Se ele apenas encapsula uma
     sequência de chamadas, remova a seção inteira. -->

## Base de conhecimento

<!-- Opcional. O que ele carrega consigo e de onde veio; que skills ou referências consulta.
     Diga também o que NÃO tem acesso — sem internet, sem banco, sem estado entre invocações,
     conforme o caso. -->

## Limites

<!-- O que ele não decide sem confirmação, o que está fora do escopo dele, e em que situação
     usá-lo é pior que não usar. Inclua a fronteira com agents e skills vizinhos. -->

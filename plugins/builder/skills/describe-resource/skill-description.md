# describe-resource

Versão 1.1.0

## O que é

Um leitor de documentação para o Creator: ele pergunta sobre um recurso que ele mesmo criou — uma
skill, um agent ou um módulo do próprio projeto — e recebe a resposta tirada do documento de descrição
daquele recurso.

## Problema que resolve

Quem constrói recursos acumula dezenas deles, e volta a cada um semanas depois. A informação de que
precisa nesse retorno — o que este recurso faz mesmo, qual era o gatilho, por que decidi que ele não
cobriria aquele caso — está escrita, mas espalhada: parte no arquivo de instrução, parte na memória de
quem escreveu.

O resultado prático é criar de novo o que já existe, ou usar um recurso fora do que ele foi desenhado
para fazer. Os dois erros vêm da mesma causa: a resposta existe e não está à mão no momento da
pergunta.

## Como funciona

O AmFlow padroniza um documento por recurso, num nome derivado do tipo e sempre na raiz da pasta dele —
`skill-description.md`, `agent-description.md`, `module-description.md`. As seções são fixas: o que é,
que problema resolve, como funciona, como usar, exemplos, em que se fundamenta, que base carrega e
quais são os limites.

Como o lugar e os títulos são conhecidos de antemão, a resposta é uma leitura direta: a skill pede ao
Builder a lista de recursos do projeto — a pasta de desenvolvimento e `.claude/` —, acha o recurso, lê o
documento na pasta dele e responde a partir da seção que corresponde à pergunta — a de uso quando se
pergunta como usar, a de limites quando se pergunta se dá para usar em determinado caso. A resposta traz
também o estado do recurso — em andamento, publicado, descontinuado — e avisa quando a versão que o
documento declara não é a do recurso.

Nada sai da máquina. Não há chamada de rede, autenticação nem consulta ao catálogo.

A regra que mais importa é negativa: quando o documento não responde, a resposta é *"o documento não
diz"*. Uma resposta plausível e inventada seria pior que a ausência, porque o Creator não teria como
distinguir uma da outra. Seção opcional que falta é outra coisa: significa que o recurso não declara
aquilo.

## Como usar

Pelo comando, que é o caminho confiável:

> `/amflow-builder:describe como usar a skill primal-branding`

> `/amflow-builder:describe o agent resource-reviewer decide sozinho ou pede confirmação?`

> `/amflow-builder:describe quais são os limites do módulo task-flow`

Não é preciso dizer o tipo nem onde o recurso está — a skill procura na pasta de desenvolvimento e em
`.claude/`, e pergunta qual é se houver ambiguidade. Sem argumento, ela lista os recursos do projeto e
pergunta sobre qual você quer saber.

Perguntar em linguagem natural, sem o comando, **costuma não acionar esta skill** — o Claude tende a
responder lendo o arquivo de instrução do recurso, que responde outra coisa. Ver *Limites*.

## Exemplos de uso

**Retomada depois de semanas.** O Creator volta a um projeto e pergunta o que a skill
`audience-segmentation` faz. Recebe a frase de abertura e o problema que ela resolve, e decide em
segundos se é ela que serve para a tarefa de hoje.

**Antes de criar algo novo.** Prestes a escrever uma skill de revisão, ele pergunta os limites da que
já existe. A seção de limites diz que ela não cobre revisão de conteúdo — o que confirma que a nova faz
sentido, em vez de duplicar a antiga.

**Recurso sem documento.** A pergunta é sobre uma skill criada antes da norma. Em vez de improvisar uma
resposta a partir do arquivo de instrução, a skill informa que não há documento e oferece criá-lo a
partir do template — lembrando que ele é obrigatório para publicar no Hub.

## Fundamentação

Norma de descrição de recurso do AmFlow.

## Limites

- Só recurso do próprio projeto; recurso de terceiro está no Hub.
- Não explica implementação — isso é do arquivo de instrução do recurso.
- `command` e `hook` não têm documento; a resposta sai do arquivo, com aviso.
- Não edita nem inventa: seção que falta é reportada como falta.
- Pergunta solta, sem o comando, costuma não acionar a skill — use o comando.

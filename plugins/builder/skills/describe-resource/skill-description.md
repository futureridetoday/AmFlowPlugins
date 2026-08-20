# describe-resource

Versão 1.0.0

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

Como o lugar e os títulos são conhecidos de antemão, a resposta é uma leitura direta: a skill deriva o
caminho a partir do tipo e do nome, lê o documento e responde a partir da seção que corresponde à
pergunta — a de uso quando se pergunta como usar, a de limites quando se pergunta se dá para usar em
determinado caso.

Nada sai da máquina. Não há chamada de rede, autenticação nem consulta ao catálogo.

A regra que mais importa é negativa: quando o documento não responde, a resposta é *"o documento não
diz"*. Uma resposta plausível e inventada seria pior que a ausência, porque o Creator não teria como
distinguir uma da outra.

## Como usar

Pelo comando, que é o caminho confiável:

> `/amflow-builder:describe como usar a skill primal-branding`

> `/amflow-builder:describe o agent reviewer decide sozinho ou pede confirmação?`

> `/amflow-builder:describe quais são os limites do módulo task-flow`

Não é preciso dizer o tipo — sem ele, a skill procura nos três e pergunta qual é, se houver ambiguidade.
Sem argumento, ela lista os recursos do projeto e pergunta sobre qual você quer saber.

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

O documento lido é o `[tipo]-description.md`, padrão definido na norma de descrição de recurso do
AmFlow. É essa norma que torna a leitura possível sem adivinhação: nome derivado do tipo, lugar fixo na
raiz do recurso, títulos de seção exatos e ordem estável.

A divisão de responsabilidade também vem dela. O arquivo de instrução de um recurso — `SKILL.md`,
`MODULE.md`, o `.md` do agent — é escrito para o agente executar, e responde *como fazer*. O documento
de descrição é escrito para uma pessoa decidir, e responde *o que é e quando cabe*. Esta skill lê o
segundo, nunca o primeiro, e é isso que a impede de devolver procedimento quando se pediu explicação.

## Base de conhecimento

Nenhuma embutida. Tudo o que a skill responde vem do documento que o próprio Creator escreveu, lido do
disco no momento da pergunta.

Ela conhece apenas o mapa entre tipo e caminho, e a lista de seções do padrão — o suficiente para achar
o arquivo e escolher de onde tirar a resposta.

## Limites

- **Só recurso de autoria própria.** Para recurso de terceiro, do catálogo, a fonte é a página no Hub
  ou a tool `get_resource` — a mesma documentação, servida pelo lado do servidor.
- **Não explica implementação.** Como o recurso faz o que faz está no arquivo de instrução dele, não
  aqui.
- **Não cobre `command` nem `hook`.** Esses dois tipos ainda não entraram na norma; a pergunta é
  respondida a partir do próprio arquivo, com o aviso de que não vem de documento de descrição.
- **Não inventa o que falta.** Seção ausente ou vazia é reportada como tal.
- **Não edita nada.** Criar ou corrigir um documento é ação separada, e só acontece se o Creator pedir.
- **Não é acionada de forma confiável por pergunta solta.** Medido em 2026-08-20, em duas rodadas: com
  a pergunta *"como usar a skill X?"* sem o comando, o Claude respondeu a partir do `SKILL.md` do
  recurso, não daqui. A causa provável é que ele já tem o arquivo à mão e responder direto parece
  bastar. **Use o comando** quando quiser a resposta do documento.

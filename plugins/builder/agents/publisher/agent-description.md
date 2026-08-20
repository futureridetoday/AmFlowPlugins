# publisher

Versão 2.0.0

## O que é

Um orquestrador de publicação: leva um recurso pronto do disco até o marketplace, passando pela revisão
de qualidade, sem os prompts editoriais do comando interativo.

## Problema que resolve

Publicar um recurso tem seis ou sete passos e nenhum deles é difícil — o problema é que errar a ordem
custa caro.

Publicar sem revisar produz submissão recusada. Publicar sem detectar que o recurso já existe cria um
recurso duplicado em vez de uma atualização. Publicar sem atualizar o cabeçalho local deixa a próxima
publicação sem o identificador que o marketplace atribuiu — e o ciclo se repete.

O comando interativo resolve isso perguntando bastante: categoria, tags, descrição, quais seções entram
no resumo de mudanças. É o certo quando o Creator quer decidir cada coisa, e é atrito puro quando ele já
decidiu tudo no cabeçalho e só quer publicar.

## Como funciona

O agent pula as perguntas **editoriais** e usa os valores que já estão no cabeçalho do recurso.

O que ele não pula é a **confirmação de publicar**. Antes de submeter, apresenta um resumo curto —
recurso, versão, cenário — e espera. Essa confirmação não tem exceção para fluxo autônomo: publicar é
ação que alcança gente fora da máquina.

A sequência é fixa. Identifica o recurso, delega ao agent de revisão e **bloqueia se ele reprovar** —
não há caminho que atravesse uma reprovação. Detecta o cenário consultando o marketplace: recurso novo
ou atualização de existente. Confirma. Submete. Atualiza o cabeçalho local com o que o marketplace
devolveu. E reporta o identificador da submissão.

O último passo é o que costuma ser esquecido numa publicação manual, e é o que faz a publicação
seguinte funcionar.

## Como usar

Delegue quando o recurso já estiver pronto e a decisão editorial já tiver sido tomada:

> Publica a skill deep-research

> Submete a atualização do agent code-reviewer ao Hub

Sem o recurso identificado no contexto, ele pergunta uma vez. Sem conector autorizado, encerra e
orienta a autorizar.

## Exemplos de uso

**Primeira publicação.** O Creator terminou uma skill. O agent revisa, detecta que é recurso novo,
confirma, submete e grava no cabeçalho local o identificador que o marketplace atribuiu.

**Atualização.** Com o identificador já presente, ele detecta o cenário de atualização, verifica se não
há submissão pendente — duas submissões abertas para o mesmo recurso é conflito, não fila — e segue.

**Reprovação na revisão.** O agent de revisão aponta problema bloqueante. A publicação para ali, com o
relatório. Não há caminho autônomo que atravesse uma reprovação.

## Fundamentação

A separação entre pular prompt editorial e manter a confirmação de publicar segue a regra de que ação
irreversível ou que alcança terceiros exige confirmação humana explícita — e fluxo autônomo não é
exceção a ela, é justamente onde ela mais importa.

A ordem revisão-antes-de-submissão existe porque o marketplace tem verificação própria: chegar lá com
problema conhecido gasta uma rodada de recusa que poderia ter sido evitada em segundos.

## Base de conhecimento

- O fluxo de publicação do AmFlow e os dois cenários — recurso novo e atualização
- As ferramentas do marketplace que consulta e usa para submeter
- Os campos do cabeçalho que o marketplace preenche na publicação e que precisam voltar para o arquivo
  local

## Limites

- **Não cria nem edita o recurso.** Publica o que já está pronto.
- **Não revisa por conta própria** — delega ao agent de revisão, e respeita a reprovação dele.
- **Não decide categoria, tags nem descrição.** Usa o que está no cabeçalho; para decidir isso, o
  caminho é o comando interativo.
- **Não publica sem confirmação**, mesmo em fluxo autônomo.
- **Não gerencia a revisão do lado do marketplace.** Submete e reporta o identificador; aprovar é de
  quem revisa lá.

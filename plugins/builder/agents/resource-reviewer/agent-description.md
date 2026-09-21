# resource-reviewer

Versão 2.0.0

## O que é

Um revisor que confere, antes da publicação, se uma skill ou um agent do Creator está pronto para ir ao marketplace — e ajuda o Creator a chegar lá.

## Problema que resolve

O marketplace recusa o que está errado, e descobrir isso ali custa uma rodada inteira: submeter, esperar, ler a recusa, corrigir e submeter de novo. Quase tudo o que ele recusa dá para achar no disco, em segundos.

Há também o que passa e não deveria: um recurso bem-formado e vazio, ainda com os marcadores do template. Ninguém é avisado, e quem o instala recebe um recurso inútil.

A revisão roda num agent à parte porque lê o recurso inteiro, os modelos e o relatório do script sem carregar nada disso na conversa do Creator.

## Como funciona

A revisão passa por quatro portões, em sequência, e **para no primeiro que reprova**:

1. **Template** — o recurso mantém a estrutura mínima que o `/amflow-builder:build` entrega para o tipo.
2. **Frontmatter** — completo pela norma do tipo, e com o que o marketplace exige do nome e da descrição.
3. **Funcionamento mínimo** — os arquivos citados existem, os scripts compilam, o corpo não tem marcador de template por preencher, e o conjunto de arquivos passa no que o marketplace recusa.
4. **Descrição** — o documento de descrição existe, tem os blocos do modelo e diz o que o recurso de fato faz.

A parte previsível é feita por um script, com o mesmo resultado a cada execução. O agent só decide o que exige leitura: se um arquivo citado é uma falha ou uma referência legítima, e se a descrição promete algo que o recurso não faz.

Ele não fala com o Creator — quem pergunta é o comando `review`. Quando um portão pode ser destravado com ajuda, o agent devolve um resultado pendente, o comando pergunta, e só com o sim do Creator o agent escreve: completa o frontmatter (o que se deriva do disco, mais propostas para o Creator aprovar) ou cria a descrição. Depois da ajuda, a revisão recomeça do primeiro portão.

## Como usar

Pelo comando `/amflow-builder:review`, que lista os recursos em andamento e deixa escolher um. Chamar o agent direto não substitui o comando: sem ele, ninguém faz as perguntas ao Creator.

Uma revisão é sempre sobre um recurso só, e o caminho do manifesto vem na chamada.

## Exemplos de uso

**Recurso pronto.** A skill passa nos quatro portões. O relatório traz `REVISADO` e, se houver, os avisos — o que não bloqueia, mas convém saber.

**Frontmatter incompleto.** A revisão para no portão 2 com `PENDENTE-FRONTMATTER`. O Creator aceita a ajuda: o agent preenche o que se deriva do disco (nome, projeto, autor, versão) e propõe descrição e tags a partir do corpo. O Creator aprova, e a revisão recomeça.

**Sem descrição, e o Creator recusa criá-la.** A revisão para no portão 4 com `PENDENTE-DESCRICAO`. Como publicar exige o documento, a recusa deixa a revisão `REPROVADO`, e o comando `review` marca o recurso como bloqueado, com o motivo registrado. Ele sai da lista de recursos em andamento até o Creator retomá-lo.

## Fundamentação

Portão de qualidade antes de um processo caro; determinismo em código, julgamento em prosa.

## Limites

- Não publica, e não consulta no marketplace o estado do recurso.
- Não revisa hook, command nem módulo: só skill e agent.
- Não julga a qualidade do texto: confere estrutura e coerência.
- Só escreve depois do sim do Creator, e só o frontmatter e a descrição.
- Passar aqui reduz a chance de recusa, mas não substitui o marketplace.

# reviewer

Versão 1.0.0

## O que é

Um revisor de qualidade para recursos do AmFlow: confere cabeçalho, corpo, segurança e conformidade
antes da publicação, e devolve um relatório dizendo se está pronto ou o que impede.

## Problema que resolve

O marketplace tem verificação própria, e ela recusa. Descobrir o problema ali custa uma rodada inteira:
submeter, esperar, ler a recusa, corrigir, submeter de novo.

Boa parte do que causa recusa é detectável em segundos no disco — campo obrigatório ausente, versão que
não supera a publicada, descrição que ainda é o texto do template.

E há uma categoria pior que a recusa: o que **passa** e não deveria. Um recurso publicado com o corpo
ainda cheio de marcadores de template funciona do ponto de vista do sistema e é inútil para quem o
instala. Ninguém é notificado disso.

## Como funciona

Quatro verificações sobre o arquivo principal do recurso — o manifesto, não a documentação ao lado.

**Cabeçalho**: campos obrigatórios e recomendados, com a distinção entre o que bloqueia e o que apenas
avisa.

**Corpo**: a verificação que mais importa e a que um validador comum não faz. Ela procura marcadores de
template não substituídos e exige substância concreta — passos reais, não estrutura vazia. Uma
descrição que ainda é o texto padrão do template é reprovada.

**Segurança**: os mesmos padrões que o fluxo de publicação aplica.

**Conformidade**: nomenclatura e estrutura de arquivos no lugar esperado.

O relatório é estruturado, separando o que bloqueia do que é aviso — e **o agent nunca edita o
recurso**. Ele aponta; corrigir é de quem escreveu.

## Como usar

Delegue antes de publicar, ou peça a revisão diretamente:

> Revise minha skill code-reviewer antes de publicar

Ele também é invocado automaticamente pelo agent de publicação, como passo obrigatório anterior à
submissão.

## Exemplos de uso

**Antes de publicar.** O Creator pede a revisão e recebe a lista de problemas separada por gravidade —
o que impede a publicação e o que é recomendação.

**Como passo de outro fluxo.** O agent de publicação o invoca sozinho. Se a revisão reprovar, a
publicação para ali.

**Recurso com template não preenchido.** O corpo ainda tem os marcadores do template. A revisão reprova
— é exatamente o caso que passaria numa verificação apenas de campos e produziria um recurso publicado
e inútil.

## Fundamentação

A ideia é a de porta de qualidade antes de um processo caro: verificar barato e localmente o que seria
verificado caro e remotamente.

A verificação de substância do corpo é o que separa este revisor de um validador de esquema. Esquema
confere forma; substância confere se há conteúdo. O modo de falha mais silencioso de um marketplace é o
recurso bem-formado e vazio.

A regra de nunca editar mantém a fronteira entre revisar e escrever: um revisor que corrige não é mais
revisor, e o autor perde a chance de aprender com o erro.

## Base de conhecimento

- O padrão de cabeçalho do AmFlow, com a distinção entre campo bloqueante e recomendado
- Os marcadores de template que indicam recurso não preenchido
- Os padrões do scanner de segurança do fluxo de publicação
- Os caminhos do arquivo principal por tipo, incluindo o layout de diretório dos agents e o anterior

## Limites

- **Não edita o recurso.** Reporta; corrigir é de quem escreveu.
- **Não publica.** Avalia se está pronto; publicar é de outro.
- **Não revisa a documentação de descrição** — o alvo é o manifesto, não o documento ao lado.
- **Não avalia uso nem avaliações** de um recurso já publicado.
- **Não substitui a verificação do marketplace.** Passar aqui reduz muito a chance de recusa, mas não a
  elimina.

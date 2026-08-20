# install-module

Versão 1.0.0

## O que é

O instalador de módulos do AmFlow: coloca um módulo dentro de uma skill que vai usá-lo, e leva uma
versão nova do módulo para todas as skills que já o adotaram.

## Problema que resolve

Dez skills que precisam da mesma capacidade produzem, hoje, dez implementações dela. Não por descuido —
porque cada skill nasce de uma conversa diferente com o modelo, e variação de interpretação é o
comportamento esperado de instrução em linguagem natural.

O custo não aparece na criação. Aparece na manutenção: uma correção vira dez correções, e nenhuma
garantia de que as dez ficaram iguais.

A tentativa manual de resolver isso é copiar arquivos entre pastas e lembrar de repetir a cópia em toda
mudança. Essa disciplina falha — e a falha é silenciosa, porque duas cópias divergentes continuam
funcionando cada uma do seu jeito.

## Como funciona

A ideia central é que **instalar e propagar são a mesma operação**. Propagar é instalar de novo, em cada
consumidor. Não há dois caminhos de código, e não deve haver: regra que vale só para um dos dois vira
divergência silenciosa.

Isso só é seguro por causa de uma regra de propriedade. Dentro de uma skill, o diretório do módulo
**pertence ao módulo e é descartável** — a instalação apaga e recopia sem perguntar. Tudo o mais
pertence à skill.

É essa regra que dispensa comparação de conteúdo, política de divergência e detecção de edição manual.
Trocou-se um mecanismo de defesa por uma regra de propriedade, que é mais barata e mais fácil de
obedecer.

Há uma exceção deliberada: a **configuração que pertence a quem adotou** fica fora do diretório do
módulo e sobrevive a toda propagação. É o que separa o que é do módulo do que é da skill.

A instalação escreve em exatamente três lugares: o diretório do módulo, uma região demarcada no arquivo
da skill, e o registro de versão no cabeçalho dela. A localização da origem é derivada da estrutura, sem
configuração a ler nem variável de ambiente.

## Como usar

Pelo comando, ou dizendo a intenção:

> `/amflow-builder:install-module`

> Instale o módulo task-flow na skill audience-segmentation

> Subi a versão do módulo — leve para quem usa

## Exemplos de uso

**Primeira adoção.** Uma skill que precisa de lista de tarefas recebe o módulo correspondente: a árvore
é copiada, a região no arquivo da skill ganha a linha do módulo e a versão fica registrada.

**Propagação de versão.** Depois de corrigir o módulo na origem, a mesma operação leva a correção a
todos os consumidores. Cada diretório é apagado e recopiado; a configuração de cada skill permanece.

**Módulo que não existe.** Pedido para instalar algo ainda não criado, ela recusa e aponta o caminho
certo — criar módulo é outro comando. Esta skill não cria.

## Fundamentação

O desenho vem de um plano com evidência medida: duas cópias do mesmo arquivo mantidas iguais à mão, num
repositório real, e um plano de refatoração que carregava uma cláusula chamada *"sincronização
obrigatória"* — cuja única função era lembrar o desenvolvedor de aplicar cada mudança nas duas cópias.

Essa cláusula é a medida exata do problema: uma regra de manutenção que só existe porque a estrutura não
a impõe. Com esta skill, ela vira um comando.

A regra de propriedade — o diretório do módulo é descartável, o resto é da skill — é o invariante do
qual todo o resto decorre, inclusive a segurança de apagar e recopiar sem perguntar.

## Base de conhecimento

- A anatomia de um módulo e o manifesto que o identifica
- Como derivar a raiz de recursos a partir da skill alvo, com as duas checagens que precisam passar
- Os três lugares que a instalação escreve, e o único que ela nunca toca
- As topologias suportadas: projeto, plugin e repositório de skills

## Limites

- **Não cria módulo.** Criar é outro comando.
- **Não edita comportamento de módulo.** Mudança se faz na origem e chega por propagação.
- **Não preserva edição feita dentro da skill.** O diretório do módulo é gerado; a próxima propagação
  sobrescreve. Só a configuração da skill sobrevive.
- **Não adivinha a raiz de recursos.** Se as checagens de estrutura não passarem, ela para e informa, em
  vez de escrever no lugar errado.

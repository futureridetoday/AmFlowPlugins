<!-- Destino: modules/<nome>/module-description.md — raiz da pasta do módulo, ao lado do
     module.json e do MODULE.md.

     Markdown puro: sem frontmatter, sem YAML, sem JSON. A identidade já vive no module.json.

     NÃO CONFUNDIR COM O MODULE.md. Os dois são prosa e ficam lado a lado, mas têm leitores
     opostos: o MODULE.md é o fragmento de instrução que o agente lê ao executar a tarefa da
     skill hospedeira; este arquivo é a explicação que o Creator lê ANTES, para decidir se
     adota o módulo. Se este arquivo começar a virar instrução de execução, o conteúdo é do
     MODULE.md.

     Módulo não é vendido no Hub e não passa pelo gate de publicação. Carrega o documento pelo
     mesmo motivo dos demais tipos: é o que responde ao Creator se vale a pena adotá-lo.

     Títulos exatos e nesta ordem. Fundamentação e Base de conhecimento são opcionais; as outras
     seis não. Subtítulos ### são livres por dentro. -->

# module-name

<!-- O valor exato do campo `name` do module.json. É identificador, não título editorial. -->

Versão 1.0.0

<!-- Linha isolada, na forma `Versão X.Y.Z`. Precisa bater com o `version` do module.json —
     ao subir a versão do módulo, subir aqui também. -->

## O que é

<!-- Uma frase, para quem não conhece o domínio: a capacidade que uma skill passa a ter por
     instalar este módulo. Fale do que a skill ganha, não do que o código faz. -->

## Problema que resolve

<!-- Por que esta capacidade virou módulo em vez de ficar dentro de cada skill. Em geral é o
     mesmo problema: escrever a mesma coisa N vezes produz N variações, e uma correção vira N
     correções sem garantia de que ficaram iguais. Diga o caso concreto. -->

## Como funciona

<!-- O mecanismo da capacidade que a skill hospedeira ganha — o que o módulo assume para si e
     o que continua sendo julgamento da skill. Se há motor determinístico, diga o que ele
     resolve e por que tirar isso do modelo importa.
     Onde o estado vive, se houver, e o que sobrevive ao fim da sessão. -->

## Como usar

<!-- Como a skill o instala e o configura: o comando de instalação, o que aparece dentro da
     skill depois, e onde fica a configuração que pertence a quem adotou.
     Diga o que é gerado e não deve ser editado — a próxima propagação sobrescreve — e o que é
     do adotante e sobrevive. -->

## Exemplos de uso

<!-- Dois a quatro cenários concretos, do ponto de vista da skill que adota: o que ela precisava,
     o que passou a fazer, e o que o usuário final percebe.
     Se há skill real usando o módulo, cite-a — adoção concreta vale mais que hipótese. -->

## Fundamentação

<!-- Opcional. Só nomes — o método, a teoria, a norma ou o padrão —, numa linha, sem explicação.
     Sem nome a citar, remova a seção inteira: seção forçada produz texto de enchimento, que é
     pior que a ausência. -->

## Base de conhecimento

<!-- Opcional. Só quando a pasta do recurso tem `references/` ou `assets/` com arquivos de dados dentro —
     pasta vazia ou só com `.gitkeep` não conta. Sem isso, remova a seção inteira — ausência não se
     declara. -->

## Limites

<!-- Lista de até cinco itens, uma frase curta cada (≈ 80 caracteres): o que o autor não oferece
     espontaneamente e quem resolve o que fica de fora. É a informação que mais evita compra
     errada e avaliação ruim. -->

# [Nome do Módulo]

<!-- Este arquivo é o fragmento de instrução do módulo — o que o agente lê quando a skill
     que o hospeda aponta para cá. Escreva para esse leitor: ele conhece a tarefa da skill,
     não conhece este módulo.

     A identidade do módulo vive no `module.json` (name, version), não em frontmatter.
     Este arquivo é prosa. -->

> **Esta é a cópia instalada — não edite aqui.** O diretório `modules/<nome>/` dentro de uma
> skill é gerado, e a próxima propagação sobrescreve tudo que houver nele. Mudanças vão para a
> origem, em `<raiz-de-recursos>/modules/<nome>/`, e chegam aqui pelo
> `/amflow-builder:install-module`. A configuração da skill, em `config/<nome>.json`, é a única
> parte que pertence a quem adotou o módulo e sobrevive à propagação.

## O que faz

<!-- A capacidade que este módulo entrega, em uma frase. O que a skill passa a conseguer fazer
     por tê-lo instalado. -->

## Quando usar

<!-- Em que ponto da tarefa da skill este módulo entra. Ser concreto: o agente precisa
     reconhecer o momento sem conhecer o módulo de antemão. -->

## Como usar

<!-- O que exige julgamento fica aqui; o que é determinístico fica no motor.
     Se o módulo tem código, diga qual arquivo invocar e com quais argumentos — e diga
     explicitamente que ele é a autoridade sobre o que resolve, para o agente não refazer à mão
     o que o script já faz.

     Exemplo:
     - Formato, ordenação e numeração são resolvidos por `motor.py` — não reproduza essas
       regras aqui nem no output.
     - O julgamento que sobra para o agente: qual item entra, e com que prioridade. -->

## Configuração

<!-- Remover esta seção se o módulo não é configurável.

     Se for, o módulo traz um `config.example.json` e a skill que o adota recebe uma cópia em
     `config/<nome>.json` na instalação. Descreva aqui cada chave: o que significa, que valores
     aceita, e o que acontece quando está ausente.

     O módulo publica a forma; a skill preenche o conteúdo. -->

## O que este módulo não faz

<!-- A fronteira. Um módulo não conhece a skill que o hospeda nem outro módulo — recebe o
     contexto pronto, por parâmetro. Se ele precisa de algo do ambiente, é a skill que fornece.

     Declarar isso aqui evita que a próxima pessoa a editar o módulo introduza um acoplamento
     que só aparece quando alguém instala o módulo em outra skill. -->

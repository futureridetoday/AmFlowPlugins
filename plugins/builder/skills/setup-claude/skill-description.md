# setup-claude

Versão 1.0.0

## O que é

O configurador do arquivo de instruções de um projeto: cria ou atualiza o `CLAUDE.md` por perguntas
guiadas, com os campos de contexto que o Claude lê em toda sessão daquele projeto.

## Problema que resolve

O arquivo de instruções é o único documento carregado automaticamente em toda sessão. Ele decide o que
o Claude sabe sobre o projeto antes da primeira pergunta: o que se está construindo, com que stack, e
que regras não podem ser quebradas.

Projeto sem esse arquivo obriga a reexplicar o contexto toda vez — e, o que é pior, aceita que o
contexto seja reconstruído por inferência, de um jeito diferente a cada sessão.

Escrevê-lo do zero também tem armadilha: a página em branco convida a descrever a arquitetura em
detalhe e esquecer o que mais importa, que são as restrições. Um projeto se protege mais dizendo o que
não pode ser feito do que descrevendo o que existe.

## Como funciona

Primeiro ela verifica se o arquivo já existe. Se existir, é lido e os campos atuais são exibidos para
revisão — a atualização parte do que está lá, nunca de uma folha em branco.

O survey cobre cinco campos: nome, descrição em uma frase, tipo de projeto, stack técnico e restrições.
Autoria e data são obtidas do ambiente, não perguntadas.

Quando o arquivo já existia, o resumo das mudanças é exibido antes de gravar. Sobrescrever um arquivo de
instruções sem mostrar o que muda é o tipo de operação que se lamenta depois.

O resultado tem estrutura fixa — identidade, visão geral, stack e restrições —, e é a estrutura que
torna o arquivo legível para quem chega, humano ou modelo.

## Como usar

Pelo comando, ou deixando o Claude detectar:

> `/amflow-builder:setup-claude`

> Configure o CLAUDE.md deste projeto

Ela também é acionada quando o Claude percebe um projeto sem arquivo de instruções.

## Exemplos de uso

**Projeto novo.** Sem arquivo de instruções, ela conduz as cinco perguntas e gera o arquivo completo,
com a estrutura padrão.

**Atualização.** Com arquivo existente, ela mostra os campos atuais, coleta o que muda e exibe o resumo
da diferença antes de gravar — nada é sobrescrito às cegas.

**Onboarding completo.** Quando o pedido é preparar um projeto inteiro, e não só o arquivo de
instruções, ela indica o comando de inicialização, que cria a estrutura de diretórios junto.

## Fundamentação

O arquivo de instruções é a aplicação mais direta da ideia de contexto persistente: informação que vale
para todas as sessões vive em arquivo, não na conversa.

A ênfase nas restrições vem da prática: instrução negativa — o que não fazer — tem mais efeito por linha
que descrição positiva, porque o modelo já infere razoavelmente o que existe, e não tem como inferir o
que é proibido.

## Base de conhecimento

- Os cinco campos do survey e a estrutura do arquivo gerado
- Como obter autoria e data do ambiente, sem perguntar
- A fronteira com o comando de inicialização de projeto, que faz mais que este

## Limites

- **Não cria a estrutura de diretórios do projeto** — para isso existe o comando de inicialização.
- **Não sobrescreve sem mostrar.** Arquivo existente vira revisão, com resumo antes de gravar.
- **Não escreve as restrições por você.** Ela pergunta; o conteúdo é de quem conhece o projeto.
- **Não configura ambiente, dependência ou ferramenta** — o arquivo é de contexto, não de setup técnico.

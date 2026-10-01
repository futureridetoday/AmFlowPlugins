# start

Versão 1.0.0

## O que é

Um comando de abertura de sessão: confere que você está logado no AmFlow e devolve, em duas linhas,
o que é o projeto em que você está trabalhando.

## Problema que resolve

Numa sessão longa, as instruções do projeto ficam distantes do ponto onde o trabalho acontece, e o
Claude passa a seguir menos o que elas pedem. Sem login, os comandos do Worker falham só no meio do
caminho, com uma mensagem que não diz que o problema é a autorização do conector.

## Como funciona

Primeiro confere o login no conector `amflow-worker`: logado, segue sem comentar; sem login, encerra
e diz como autorizar. Depois relê as instruções do projeto — `.claude/CLAUDE.md` e, se existir, o
`CLAUDE.md` da raiz — e resume a identidade do projeto a partir do título e da visão geral. Não
escreve nada e não altera estado.

## Como usar

Digite `/amflow-worker:start` no início da sessão, ou quando quiser recolocar as instruções do
projeto em foco. O Claude não o dispara sozinho. Você precisa do conector `amflow-worker`
autorizado pelo `/mcp`.

## Exemplos de uso

- **Início do dia.** Você abre o Claude Code no projeto e digita `/amflow-worker:start`. Recebe duas
  linhas com o nome e o propósito do projeto, e segue trabalhando com as instruções frescas no
  contexto.
- **Conector não autorizado.** Você roda o comando numa máquina nova. Em vez do resumo, recebe a
  orientação de autorizar o conector `amflow-worker` pelo `/mcp` e repetir o comando.
- **Projeto sem configuração.** Você roda o comando numa pasta sem `.claude/CLAUDE.md`. O comando
  diz que o projeto não está configurado e encerra.

## Limites

- Não funciona offline: depende do login no AmFlow.
- Não lista regras, recursos nem o estado do git — só a identidade do projeto.
- Não cria nem corrige o `CLAUDE.md` de um projeto não configurado.
- Não verifica licença nem atualização de recurso instalado.

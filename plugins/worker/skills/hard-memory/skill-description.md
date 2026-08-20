# hard-memory

Versão 1.0.0

## O que é

Um protocolo de memória em arquivo para agents: o agent lê o que aprendeu antes de começar e registra o
que aprendeu ao terminar, para que a próxima sessão comece sabendo.

## Problema que resolve

Um agent recomeça do zero a cada sessão. Isso é aceitável para tarefa isolada e péssimo para trabalho
continuado.

O custo aparece em repetição: o usuário reexplica a mesma preferência, o agent refaz uma decisão que já
tinha sido tomada e descartada, e comete de novo o erro que já cometeu — sem qualquer sinal de que está
repetindo.

A solução ingênua — guardar tudo — troca um problema por outro. Um arquivo de memória que cresce sem
disciplina é lido inteiro a cada sessão e consome justamente o contexto que deveria liberar.

## Como funciona

Cada agent com memória ativada tem um arquivo próprio, no projeto ou na pasta do usuário quando a
memória deve valer para todos os projetos.

O arquivo tem seções fixas: contexto do projeto, preferências do usuário, estado de tarefas, decisões
registradas e aprendizados.

**O que entra é tão importante quanto o que fica de fora.** Entram preferências observadas, decisões com
o motivo, padrões do projeto, tarefas em andamento e erros com a forma de evitá-los. **Não entram**
conteúdo de arquivo, resultado intermediário de ferramenta, nem qualquer coisa recuperável lendo o
projeto — memória não é cache.

São três protocolos. **Leitura** no início da sessão, antes de qualquer tarefa. **Escrita** depois de
cada tarefa concluída, não só no fim da sessão — sessão interrompida é o caso em que a memória mais
importa. E **compactação**, disparada quando o arquivo passa de um limite de linhas: o conteúdo antigo
vai para um arquivo de histórico e o principal é consolidado.

O arquivo de histórico existe só para auditoria humana e nunca é lido automaticamente. É o que impede a
memória de crescer para sempre.

## Como usar

Não é invocada diretamente — quem a usa é um agent que declara memória ativa no próprio cabeçalho,
escolhendo escopo, estratégia de escrita e limite de compactação.

Ao criar um agent pelo `/amflow-builder:build`, há um passo que oferece ativar a memória e cuida da
configuração.

## Exemplos de uso

**Preferência que não precisa ser repetida.** O usuário corrige o agent uma vez sobre como quer o
relatório. A correção entra em preferências, e a sessão seguinte já entrega no formato certo.

**Tarefa interrompida.** A sessão cai no meio de um trabalho de cinco etapas. Como a escrita acontece a
cada etapa concluída e não só no fim, a retomada sabe onde parou.

**Arquivo crescendo.** Ao passar do limite de linhas, o conteúdo antigo é arquivado e o principal é
consolidado — o agent continua com memória sem pagar contexto crescente por ela.

## Fundamentação

A separação entre memória e cache é o que sustenta o desenho: memória guarda o que não pode ser
redescoberto, e tudo que pode ser lido do projeto fica de fora. Sem essa regra, o arquivo vira uma cópia
degradada do repositório.

A escrita após cada tarefa, e não ao final da sessão, vem da observação de que sessões terminam de
formas que ninguém planeja.

A compactação com arquivamento resolve o conflito entre continuidade e custo: o histórico completo
sobrevive para auditoria, e o que é lido a cada sessão permanece pequeno.

## Base de conhecimento

- O esquema do arquivo de memória e o que cada seção guarda
- O critério do que persiste e do que não persiste
- Os três protocolos: leitura, escrita e compactação
- Os caminhos por escopo, e o arquivo de histórico

## Limites

- **Não é para uso direto.** É infraestrutura de agents, não recurso invocável.
- **Não é adquirível no marketplace** — vem instalada com o plugin.
- **Não resolve sessões paralelas.** Duas sessões do mesmo agent escrevendo ao mesmo tempo: a última
  vence, e não há mesclagem.
- **Não substitui o repositório.** O que pode ser lido do projeto não deve estar aqui.
- **Não é gratuita em contexto.** O arquivo é lido inteiro a cada sessão; sem disciplina no que
  persiste, o custo cresce.
- **Ausente, não quebra.** Agent sem a skill instalada deve seguir sem memória.

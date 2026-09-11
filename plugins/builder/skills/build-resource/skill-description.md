# build-resource

Versão 1.0.0

## O que é

O criador de recursos do AmFlow: produz a estrutura completa de uma skill, agent ou
módulo — já com o cabeçalho preenchido e o documento de descrição ao lado. Para skill, o Creator
escolhe o método: survey guiado, importar um recurso existente e adaptá-lo, ou partir do template
puro. Agent e módulo partem do template com o nome. (Redução temporária: hook, command e plugin
saem até cada tipo ter seu fluxo. Workflow sai em definitivo — a autoria migra para módulo.)

## Problema que resolve

Criar um recurso do zero exige acertar uma dúzia de decisões que só parecem pequenas: o nome no formato
certo, o tipo correto, a descrição que outro Claude vai ler para decidir quando invocar, a vertical, o
tipo de saída, as tags.

A que mais custa é a descrição. Ela é o que o marketplace indexa e o que decide se o recurso é
encontrado — e é escrita no fim, com pressa, por quem já gastou a atenção nas outras onze.

Há também uma confusão recorrente entre dois tipos: skill e módulo. Quem erra descobre tarde, quando o
recurso está no lugar errado da árvore e o usuário não consegue invocá-lo — ou consegue, e não deveria.

## Como funciona

Uma pergunta por vez, adaptando cada pergunta às respostas anteriores.

Antes de tudo há um passo de autenticação, e ele **encerra o processo se falhar** — sem sessão
autorizada, nenhum arquivo é criado. É o que garante que a autoria do recurso fique registrada desde a
origem.

Depois do tipo, para **skill**, vem a escolha do método. **Passo a passo** roda o survey guiado
completo. **Importar** lê um recurso que já existe, monta um plano de adaptação aos padrões do AmFlow
e cria depois da confirmação do Creator. **Usar template** pede só nome, descrição e tags, e entrega
o esqueleto. **Agent e módulo** não têm escolha de método enquanto cada um não ganha seu
fluxo dedicado: pedem o nome e partem do template.

O survey é o de skill. Para módulo, não há cabeçalho a preencher — a identidade dele mora em outro
arquivo; agent parte do template e o Creator preenche o conteúdo depois.

A descrição recebe tratamento próprio: a skill gera três sugestões e oferece rodadas de refinamento até
o Creator confirmar, com um enquadramento explícito — *escreva como se estivesse briefando um colega sem
contexto*.

A fronteira entre skill e módulo é resolvida por uma pergunta única: **quem dispara?** Se a resposta for
"a skill", é módulo.

No fim, os arquivos são criados a partir dos templates — e skill, agent e módulo nascem com o
`[tipo]-description.md` junto, que é obrigatório para publicar.

## Como usar

Pelo comando, ou dizendo o que quer criar:

> `/amflow-builder:build`

> Quero criar uma skill de revisão de código

Se o recurso já existir no destino, ela encerra e orienta a editar direto ou publicar — não sobrescreve.

## Exemplos de uso

**Skill nova.** O Creator diz o que quer; a skill conduz vertical, função, exemplos de uso, tipo de
saída, descrição com refinamento, nome e tags — e entrega a pasta pronta, com o documento de descrição
esperando conteúdo.

**Dúvida entre skill e módulo.** Perguntado quem dispara a capacidade, o Creator responde "a skill que
vai usar" — e o tipo se resolve sozinho, antes de qualquer arquivo existir.

**Sem conector autorizado.** A skill encerra no passo de autenticação e explica como autorizar, em vez
de criar arquivos com autoria vazia que precisariam ser corrigidos depois.

## Fundamentação

O formato de survey guiado existe porque a qualidade de um recurso é decidida antes da primeira linha:
nome, tipo e descrição são as escolhas de maior efeito e as mais fáceis de errar sozinho.

O tratamento especial da descrição vem da constatação de que ela tem dois leitores — o marketplace, que
a indexa, e outro Claude, que decide invocar com base nela. Um campo com dois leitores automáticos não
pode ser escrito no piloto automático.

A criação do documento de descrição junto com o recurso segue a norma de descrição de recurso do
projeto: recurso sem esse documento não passa no gate de publicação, e criá-lo depois é retrabalho.

## Base de conhecimento

- Os três tipos de recurso (skill, agent, module) e o destino de cada um, em pasta irmã de `.claude/` no projeto
- Os templates de cada tipo, incluindo os três de documento de descrição
- A taxonomia de verticais e funções usada no survey
- As regras de nome: minúsculas e hífens, sem hífen inicial, final ou consecutivo, até 64 caracteres

## Limites

- **Não preenche o conteúdo do recurso.** Entrega a estrutura e o cabeçalho; o corpo é de quem cria.
- **Não sobrescreve recurso existente.**
- **Não cria mais de um recurso por execução** sem pedido explícito.
- **Não funciona sem conector autorizado** — encerra no passo de autenticação, sem criar nada.
- **Não publica.** Publicar é outro comando, depois do recurso pronto.

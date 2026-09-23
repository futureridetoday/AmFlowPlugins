# resource-publisher

Versão 1.0.0

## O que é

Quem envia ao Hub AmFlow um recurso que já passou pela revisão — a última etapa do `/amflow-builder:publish`, depois que o Creator confirmou.

## Problema que resolve

Antes deste agent, o `publish` enviava o que quisesse: um recurso que a revisão reprovaria passava e o Hub aceitava, porque nada entre o Creator e a tool `publish` conferia o status. O `resource-publisher` é a barreira final — reconfere, no instante do envio, que o recurso ainda está `reviewed`, e envia exatamente o que a revisão aprovou, sem limpar nem ajustar nada na cópia.

## Como funciona

Recebe um recurso já escolhido e confirmado pelo comando, roda o script `publish.py` sobre ele — que barra qualquer coisa fora de `reviewed` e monta o pacote a enviar —, e só então chama a tool `publish`. Só grava o `amflow-hub-id` e o `amflow-status: pending_review` localmente depois que o Hub aceita; numa recusa, nada muda no disco.

Ele não conversa com o Creator. Preço, changelog e a confirmação de publicar são perguntas do comando `/amflow-builder:publish`, feitas antes de invocá-lo — este agent é chamado uma única vez, já com tudo decidido.

## Como usar

Pelo comando `/amflow-builder:publish`, que lista os recursos `reviewed`, conduz a conversa e invoca este agent só depois da confirmação. Chamar o agent direto não substitui o comando: sem ele, ninguém faz as perguntas nem mostra a prévia.

## Exemplos de uso

**Publicação nova.** O Creator confirma preço e prévia de uma skill `reviewed` sem `hub_id`. O agent roda `publish.py`, confirma a camada 1, envia e devolve `hub_id` e `submission_id` — o comando grava e mostra o resumo.

**Recurso deixou de estar `reviewed`.** Entre a listagem e a confirmação, o recurso foi editado e perdeu o status. O agent roda `publish.py` de novo, recebe `BARRADO` e devolve isso ao comando — a tool `publish` nunca é chamada.

**O Hub recusa.** A versão local não supera a de produção, ou o bundle falha na validação. O agent devolve o erro do Hub tal como veio, e nada é gravado localmente.

## Fundamentação

Camada 1 de um scanner de segurança em camadas: o status é o que separa o que a revisão aprovou do que ainda não passou por ela.

## Limites

- Não revisa o recurso — a camada 1 só confere o status que a revisão já gravou.
- Não decide preço, changelog nem cenário — chegam prontos na chamada.
- Não consulta o Hub além do envio: submissão pendente e versão em produção são checagens do comando, antes de chamar este agent.
- Não publica hook, command nem módulo — a revisão, de onde vem o `reviewed`, cobre só skill e agent.

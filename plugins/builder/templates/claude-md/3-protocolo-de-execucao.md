---

## Protocolo de Execução

### Diretrizes obrigatórias

- **Aprovação antes de executar**: nunca executar um plano sem aprovação explícita do usuário. Apresentar o plano, aguardar confirmação, só então agir.
- **Escopo exato**: executar apenas o que foi solicitado. Qualquer adição ao escopo exige aprovação prévia.

### Leitura e diagnóstico

Ações de leitura e observação nunca precisam de confirmação: ler arquivos, executar `git status`, `git log`, `ls`, `find`, `grep` e equivalentes. Não alteram estado — podem ser feitas a qualquer momento.

### Comandos explícitos do usuário

Quando o usuário diz o que fazer ("crie o arquivo X", "renomeie Y para Z"), o pedido é a aprovação. Executar na ordem exata e no escopo exato do que foi pedido — sem adicionar etapas, sem expandir o escopo.

### Planos e ações irreversíveis

Sempre apresentar antes de executar e aguardar aprovação explícita quando:
- Claude propõe uma sequência de ações não solicitada pelo usuário
- A ação é irreversível: deletar arquivos, push, deploy, alterações em banco ou serviços externos
- O impacto afeta mais de 5 arquivos ou envolve dependências externas

### Ambiguidade

Quando a tarefa for ambígua ou o escopo não estiver claro:
1. Declarar o entendimento em uma frase
2. Aguardar confirmação antes de prosseguir
3. Nunca assumir e executar

### Sugestões não solicitadas

Apresentar e aguardar aprovação explícita. Nunca aplicar mudanças não pedidas, mesmo que pareçam melhorias óbvias.

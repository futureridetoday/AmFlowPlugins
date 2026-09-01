---

## Protocolo Anti-Alucinação

### Regra Principal

Verificar antes de afirmar. Nenhuma informação sobre o estado do sistema, arquivos ou código deve ser declarada sem evidência obtida via ferramentas na sessão atual.

### Ao Compartilhar Resultados

- Citar a evidência exata: arquivo, linha ou comando que gerou a informação
- Nunca assumir que um arquivo, função ou configuração existe sem lê-lo primeiro
- Memórias de sessões anteriores são ponto de partida, não verdade — verificar antes de usar

### Quando Faltam Dados

1. Listar as fontes consultadas
2. Declarar explicitamente a limitação: "Não encontrei evidências de..."
3. Solicitar o input mínimo necessário para prosseguir

### Quando a Verificação Passa e a Conclusão Erra

Verificar não basta se a verificação não podia responder a pergunta. Os cinco casos abaixo produzem
conclusão errada **com a regra principal sendo cumprida** — houve ferramenta, houve evidência, e o
resultado estava errado assim mesmo.

- **Ausência de evidência não é evidência de ausência.** Não encontrar não é encontrar que não
  existe. Antes de concluir que algo não existe, não funciona ou foi recusado, perguntar se o método
  usado seria capaz de mostrar o contrário caso o contrário fosse verdade.
- **Oráculo de aceitação não é oráculo de efeito.** Uma interface aceitar um valor não prova que o
  valor produz efeito; um campo voltar vazio não prova que foi ignorado — pode ser só o que aquela
  interface não expõe. Efeito só se afirma observando o efeito.
- **Medição sem controle não mede.** Antes de rodar, declarar qual resultado falsificaria a
  hipótese. Medida que daria o mesmo número com e sem a causa não é evidência de nada.
- **Estado em cache responde pelo passado.** Lista sincronizada no início da sessão, índice
  construído antes da mudança, resultado de ferramenta guardado de antes — todos respondem sobre o
  momento em que leram, não sobre agora. Se a mudança veio depois, reler do zero antes de concluir.
- **Pergunta não respondível não vira "não".** Quando o canal disponível não alcança a pergunta, o
  resultado é "não sei por este caminho" — e isso se declara como tal, em vez de virar resposta
  negativa.

### Proibido

- Inventar nomes de funções, arquivos, flags ou configurações
- Assumir o estado do sistema sem confirmação via ferramenta
- Afirmar que algo "funciona" ou "existe" sem ter verificado na sessão atual
- Ocultar incertezas ou limitações identificadas

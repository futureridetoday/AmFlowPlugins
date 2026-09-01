# AmFlowPlugins — Instruções do Projeto

## Visão geral

Catálogo público dos plugins do AmFlow para o Claude Code — a fonte que `/plugin marketplace add`
lê. Aqui vive só o necessário para publicar, instalar e atualizar o marketplace e os dois plugins:
`amflow-worker` e `amflow-builder`.

## Mapa do repositório

| Caminho | O que vive aqui |
|---|---|
| `.claude-plugin/marketplace.json` | Catálogo — declara as duas entradas de plugin |
| `plugins/worker/` | Plugin `amflow-worker` |
| `plugins/builder/` | Plugin `amflow-builder` |
| `plugins/builder/templates/claude-md/` | Os cinco fragmentos de conduta — fonte das seções deste arquivo |
| `.github/workflows/plugins.yml` | Guard de publicação — valida manifestos e frontmatter |
| `scripts/check-surface.py` | Guard de publicação — separação de superfícies MCP |

## Formato do `marketplace.json`

Declara `name`, `description`, `owner` e a lista `plugins` — cada entrada com `name`, `source`
(caminho relativo, ex.: `./plugins/worker`) e `description`. `source` é sempre um caminho dentro
deste repositório, nunca uma URL externa.

## Invariantes

- Os identificadores instalados não mudam: `amflow-worker@amflow` e `amflow-builder@amflow`.
  Renomear qualquer um dos dois — plugin ou marketplace — deixa quem já instalou com uma entrada
  órfã.
- `version` mora em cada `plugin.json` do respectivo plugin. Nunca é derivada da fonte (hash de
  commit, data) — é o que o Claude Code exibe como versão instalada.
- Este repositório é público. Nenhum arquivo aqui cita infraestrutura, documentação interna ou
  identificadores do repositório de desenvolvimento do AmFlow.
- Nada que o plugin distribui pode apontar para o repositório de desenvolvimento. Ponteiro que
  resolve aqui e morre no destino é o defeito mais recorrente deste projeto — ocorreu na unidade
  0003-04 do Worker, foi corrigido, e voltou em quatorze ocorrências no Builder. Quando o ponteiro
  carrega informação, inlinar a informação; quando o próprio recurso já a cobre, cortar.

## Este repositório não é onde se desenvolve

É o pacote, não a oficina. Plano, correção, melhoria e evolução dos plugins acontecem no repositório
de desenvolvimento do AmFlow, privado, e chegam aqui já decididos — como conteúdo de `plugins/` ou
como entrada no catálogo.

Isso vale inclusive para uma correção que parece pequena. Editar direto aqui produz uma versão que
não existe do outro lado, e nada neste repositório avisa quando os dois divergem: não há teste, não
há guard de paridade, não há CI que compare. Foi o argumento que aposentou o canal npm — manter dois
artefatos que deveriam andar juntos produz deriva, e a deriva só aparece quando alguém depende da
metade errada.

Os dois guards que rodam aqui — `plugins.yml` e `check-surface.py` — validam o que está prestes a ser
publicado. Não substituem a revisão que acontece do outro lado.

### Como exceder a regra

A regra é excedível, e o caminho é declarado para não virar pergunta repetida a cada sessão:

1. **O override é explícito e do mantenedor.** Não se infere de "pode corrigir" nem de urgência.
   Perguntar uma vez, com a consequência nomeada; resposta afirmativa vale para o trabalho em curso.
2. **Perguntar uma vez, não a cada arquivo.** Override concedido cobre a sessão. Repetir a pergunta
   é atrito, não zelo.
3. **O que foi editado aqui precisa ser replicado do outro lado.** Ao encerrar o trabalho, listar os
   arquivos tocados — é o único registro de divergência que existe.

## Git

- **Commit direto em `main`.** Este repositório não usa branch de trabalho.
- **Nunca criar branch sem permissão explícita.**
- Nunca fazer force push em `main`.
- Nunca fazer push sem pedido — commit e push são atos separados aqui.

## Frontmatter dos recursos do plugin

Os recursos dentro de `plugins/` têm frontmatter, e **a forma difere por tipo**:

- **`skill`** — segue a especificação Agent Skills. No topo vivem só `name`, `description`,
  `license` e os campos condicionais da spec. Todo dado do AmFlow vive em `metadata`, com prefixo
  `amflow-` e valor sempre string. **Não existe `type`, `version`, `status` nem `created` no topo de
  uma skill.**
- **`agent`, `command`, `hook`** — frontmatter YAML comum, com `name`, `type`, `description`,
  `version`, `status` e o resto no topo.

Confundir as duas formas é o defeito que reprovava toda skill gerada pelo próprio Builder. A tabela
de referência por tipo está em [`plugins/builder/agents/reviewer/reviewer.md`](../plugins/builder/agents/reviewer/reviewer.md),
passo 4.

O `plugins.yml` **não valida a forma** — confere só que a primeira linha do arquivo é `---`. Ausência
de erro no CI não é evidência de frontmatter correto.

## Este arquivo não tem frontmatter

E não é esquecimento. O Claude Code entrega o `CLAUDE.md` como mensagem de usuário e não interpreta
bloco YAML no topo — frontmatter aqui é texto que consome contexto em toda sessão sem ser lido por
nada. É a mesma regra que o `/amflow-builder:new-project` aplica ao gerar o `CLAUDE.md` de um projeto
novo.

## Sobre as cinco seções abaixo

São cópia literal dos fragmentos em `plugins/builder/templates/claude-md/`, os mesmos que o
`/amflow-builder:new-project` injeta no `CLAUDE.md` de todo projeto criado. Ficam inline porque regra
de conduta precisa estar no contexto, não a um `Read` de distância.

Alterou o fragmento, atualizar aqui — e vice-versa. Diferente de tudo mais neste repositório, os dois
lados desta cópia moram aqui, então a divergência é verificável por diff.

---

## Idioma e Nomenclatura

### Comunicação e Documentação

- Todo conteúdo de chat, documentação e markdown em **pt-BR**
- Acentuação obrigatória: `não` (nunca `nao`), `você` (nunca `voce`), `próximo` (nunca `proximo`)
- Termos técnicos, nomes de frameworks e metodologias permanecem em inglês

### Código

- Identificadores (variáveis, funções, classes, módulos) em **inglês**
- Comentários inline e docstrings em **pt-BR**
- Strings voltadas ao usuário final em **pt-BR**

### Nomenclatura de Arquivos e Diretórios

| Contexto | Padrão | Exemplo |
|---|---|---|
| Diretórios | kebab-case | `claude-md/` |
| Arquivos Markdown | kebab-case | `global.md` |
| Arquivos de configuração | kebab-case | `plugin.json` |
| Scripts shell | kebab-case | `pre-tool-use.sh` |
---

## Comunicação

### Tom e Estilo

- Linguagem profissional, neutra e objetiva
- Respostas curtas e diretas ao ponto
- Sem emojis, floreios, reforços emocionais ou chamadas motivacionais
- Sem espelhamento de comunicação do usuário
- Sem transições decorativas entre seções

### Formato de Respostas

- Entregue apenas o necessário para avançar o trabalho
- Para perguntas exploratórias: resposta direta em 2-3 frases com recomendação e tradeoff principal
- Para tarefas: execute e reporte resultado — não narre o processo
- Ao referenciar código: cite `arquivo:linha` para navegação direta

### O que Eliminar

- Resumos do que acabou de ser feito ("fiz X, Y e Z")
- Perguntas brandas ("posso ajudar com mais alguma coisa?")
- Confirmações desnecessárias do que o usuário disse
- Comentários sobre a qualidade da pergunta ou tarefa
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
---

## Uso de Ferramentas

### Hierarquia de Ferramentas

1. Ferramentas dedicadas têm prioridade sobre Bash (Read, Edit, Write)
2. Bash apenas para operações exclusivas de shell
3. Agent para exploração ampla que consumiria mais de 3 queries no contexto principal

### Regras de Arquivo

- Leitura: sempre usar `Read`, nunca `cat` / `head` / `tail`
- Edição: sempre usar `Edit` para arquivos existentes
- Criação: usar `Write` apenas para arquivos novos ou reescrita completa
- Nunca usar `echo >` ou `cat <<EOF` para escrever arquivos

### Paralelismo

- Chamadas independentes de ferramentas devem ser feitas em paralelo na mesma mensagem
- Chamadas dependentes devem ser sequenciais — nunca usar placeholders ou adivinhar valores intermediários

### Bash

- Sempre usar paths absolutos
- Caminhos com espaços entre aspas duplas
- Nunca usar flags interativas (`-i`) em comandos git ou outros
- Preferir `find .` ao invés de `find /` para evitar varredura completa do sistema

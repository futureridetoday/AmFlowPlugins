---
# about
name: review
type: command
project: AmFlow
description: Lista os recursos do Creator em andamento e revisa o escolhido em quatro portões — template, frontmatter, funcionamento mínimo e descrição — pelo agent resource-reviewer. Oferece ajuda para completar o frontmatter e escrever a descrição, e nunca publica
tags: [review, quality, resource-reviewer, creator]

# history
author: Bortoli
created: 2026-09-13
status: draft
version: 2.1.0
updated: "2026-09-21"

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-builder:review

Lista os recursos do Creator com status `in_progress`, deixa escolher um, e o revisa em quatro portões
pelo agent `resource-reviewer`. É o único chamador do agent: o subagente não pergunta ao usuário, então
toda pergunta — aceitar ajuda, aprovar uma proposta — é feita aqui, e o agent só devolve o que ficou
pendente. Nunca publica.

## Quando usar

- "revisa a skill deep-research antes de eu publicar"
- "quais recursos estão prontos para eu revisar?"
- "valida esse agent antes de submeter"

## Quando não usar

- "publica a skill deep-research" — é `/amflow-builder:publish`
- "qual o status da minha skill no Hub?" — é `/amflow-builder:publish-status`, que consulta o Hub; a
  revisão não consulta o estado do recurso lá
- "marca a skill como pausada" ou "retoma a skill bloqueada" — é `/amflow-builder:status`

## Processo

### Fase 1 — Listar recursos em andamento

1. Resolver o projeto — `$CLAUDE_PROJECT_DIR` quando definido; senão, o diretório de trabalho atual.
   É o `<projeto>` dos comandos abaixo, sempre como caminho absoluto.

2. Chamar o script, nunca reimplementar a varredura:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" list <projeto> --status in_progress
   ```

3. Ler a saída, nunca reformular o julgamento do script:

   | Saída | O que fazer |
   |---|---|
   | Código 0, com tabela | Reproduzir a tabela markdown tal como veio — cabeçalho e linhas |
   | Código 0, sem tabela (lista vazia) | Encerrar: **"Nenhum recurso em andamento encontrado."** |
   | Código 1 | Alguma linha começa com `ERRO` — exibir junto da tabela, não esconder |

### Fase 2 — Escolher o recurso

4. Perguntar ao Creator qual item da tabela revisar — por tipo/nome, ou pela linha. **Um recurso por
   execução**, nunca revisar a lista inteira em lote.

5. Item ambíguo ou fora da tabela → mostrar a tabela de novo e perguntar. Nunca adivinhar.

6. **Barreira de tipo.** A revisão cobre só `skill` e `agent`. Para os outros, responder com a mensagem
   do tipo e encerrar, **sem invocar o agent**:

   | Tipo | Mensagem |
   |---|---|
   | `module` | "Módulos não passam pela revisão porque ainda não são distribuídos pelo Hub. Um módulo é uma biblioteca que você usa nas suas skills, não um recurso publicado por conta própria." |
   | `hook`, `command` | "A revisão ainda não cobre `<tipo>`. Por enquanto, só skills e agents são revisados." |

7. **O caminho do manifesto** é a coluna `Local` da linha escolhida, relativo ao `<projeto>` — é ele que
   o agent recebe. Se o mesmo `tipo`/`nome` aparece em duas linhas, uma com `Local` sob `.claude/` e
   outra sem, revisar a da pasta de desenvolvimento (a sem `.claude/`) e avisar em uma linha que há
   cópia em uso em `.claude/`: a pasta de desenvolvimento é a fonte, e `.claude/` guarda o que está em
   uso. Existindo só a cópia em `.claude/`, seguir nela.

### Fase 3 — Revisar

8. Invocar o agent com o identificador **registrado**, que carrega o nome da pasta do agent — o nome
   curto `resource-reviewer` não resolve:

   ```
   Agent(
     subagent_type: "amflow-builder:resource-reviewer:resource-reviewer",
     run_in_background: false,
     prompt: "Modo: revisar\nProjeto: <projeto>\nLocal: <caminho do manifesto>"
   )
   ```

   O `run_in_background: false` pede o relatório na própria chamada, mas nem sempre vale: na sessão
   interativa o `Agent` pode lançar o agent em segundo plano mesmo assim. Se a resposta da chamada disser
   que ele foi lançado em segundo plano, o relatório chega depois, como mensagem do subagente. Então
   **esperar**: no máximo uma linha dizendo que a revisão está em andamento, sem adivinhar o veredito e sem
   seguir para o ramo antes do relatório. Quando ele chegar, tratá-lo como o retorno da chamada. A
   notificação de término que vem em seguida só avisa que o agent acabou: não é resposta do Creator, não
   leva comentário e não repete a pergunta que já foi feita. Vale para toda invocação do agent neste
   comando.

9. Ler a linha `RESULTADO:` do relatório e seguir o ramo. Reproduzir o relatório tal como veio —
   cabeçalho, `RESULTADO`, problemas e avisos —, nunca reformulando o veredito nem resumindo os
   problemas, e só então acrescentar a mensagem do ramo:

   | `RESULTADO` | O que fazer |
   |---|---|
   | `REVISADO` | Registrar a revisão (abaixo), dizer que o recurso passou nos quatro portões e ficou `reviewed`. Publicar é `/amflow-builder:publish` |
   | `REPROVADO`, `PORTAO: 1` | Dizer que é preciso usar o padrão do AmFlow (`/amflow-builder:build`) para produzir qualquer recurso, e que a revisão foi concluída |
   | `REPROVADO`, `PORTAO: 2` | O nome do recurso começa por número. Dizer que o Hub o recusa e que renomear é decisão do Creator — a pasta, o `name`, o título da descrição e as referências no corpo. Sem oferta de ajuda, sem `blocked` |
   | `REPROVADO`, `PORTAO: 3` | Dizer o erro e que é preciso corrigir e refazer a revisão |
   | `PENDENTE-FRONTMATTER` | Ramo A |
   | `PENDENTE-DESCRICAO` | Ramo B |
   | `ERRO` | Exibir a mensagem e encerrar |

   Dois `REPROVADO` do mesmo relatório não são o mesmo caso: o portão está na linha `PORTAO:`.

   **Registrar a revisão.** No `REVISADO` do agent, e só nele, rodar o script. Ele refaz a revisão
   determinística e só grava `reviewed` se o resultado ainda for `REVISADO` e o recurso estiver em
   `in_progress`, que é o status da lista da Fase 1:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" <projeto> <local> --registrar
   ```

   `<local>` é o caminho do manifesto do passo 7. O script imprime o relatório de novo: não repeti-lo,
   só ler o código de saída e a linha `REGISTRADO:`.

   | Saída | O que fazer |
   |---|---|
   | Código 0, com `REGISTRADO:` | Reproduzir essa linha e dizer que o recurso ficou `reviewed` |
   | Código 1 | O script não confirmou o `REVISADO` do agent, e é ele que decide o piso. Reproduzir o `RESULTADO` do script, dizer que nada foi gravado e que é preciso corrigir e refazer a revisão |
   | Código 2 | Exibir a linha `erro:`, dizer que o recurso passou na revisão mas o status não foi gravado, e nunca editar o arquivo à mão. Se o `erro:` disser que o recurso não está em `in_progress`, o status mudou depois da listagem: para revisar, o Creator o retoma com `/amflow-builder:status` |

#### Ramo A — frontmatter incompleto

10. Mostrar os problemas do portão 2 e, se o relatório trouxe `PROPOSTA-DESCRIPTION`, a proposta. Perguntar
    ao Creator se quer ajuda para completar o frontmatter.

11. **Recusou.** Gravar `blocked` com o motivo e informar `REPROVADO`:

    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" set <projeto> <tipo>/<nome> blocked --motivo "<motivo>"
    ```

    O motivo é uma linha: o que faltava e que o Creator recusou a ajuda, com a data de hoje. O `status.py`
    é o único caminho de escrita do status — nunca editar o arquivo à mão. Dizer também que o recurso
    saiu da lista de recursos em andamento, e que para revisá-lo de novo o Creator o retoma com
    `/amflow-builder:status`.

12. **Aceitou.** Invocar o agent com `Modo: completar-frontmatter` (mesmo formato do passo 8). Ele
    escreve o que se deriva do disco e devolve `PROPOSTAS` para o que é conteúdo do Creator:
    `description`, `tags`, `license` em skill; `d1`, `d2`, `d4` em agent.

    - Mostrar **todas** as propostas de uma vez e perguntar se o Creator aprova ou edita.
    - `PENDENTE: author` → o `git config user.name` estava vazio: perguntar o nome do autor e incluí-lo.
    - `AUTOR-ID: indisponível` → a sessão do conector `amflow-builder` não está autorizada: orientar a
      autorizar pelo `/mcp`. O `author_id` fica sem valor, e o portão 2 avisa.
    - `STATUS: ausente` → gravar `in_progress` pelo `status.py set`, sem `--motivo`.
    - Aprovadas: invocar o agent de novo, com `Modo: completar-frontmatter` e um bloco `Aprovados:` com
      uma linha `campo: valor` para cada valor final. Não aprovadas: é recusa, e vale o passo 11.

13. Reinvocar `Modo: revisar` — a revisão **recomeça pelo portão 1**. A ajuda de frontmatter é oferecida
    **uma vez por execução**: se o relatório voltar `PENDENTE-FRONTMATTER` outra vez, tratar como
    `REPROVADO`, mostrar o que sobrou como correção manual, e **não** gravar `blocked` — o Creator não
    recusou nada.

#### Ramo B — descrição ausente ou com erros

14. Ler o `MOTIVO:` do relatório:

    | `MOTIVO` | O que dizer e perguntar |
    |---|---|
    | `ausente` | O documento de descrição é obrigatório: publicar no Hub exige `<tipo>-description.md`, que é o texto da página de detalhe do recurso. Oferecer criá-lo |
    | `com-erros` | Mostrar os erros do portão 4 e oferecer a correção |

15. **Recusou.** Gravar `blocked` com o motivo (passo 11), informar `REPROVADO` e repetir que publicar no
    Hub exige o documento de descrição.

16. **Aceitou.** Invocar o agent com `Modo: escrever-descricao`, mais um bloco `Erros:` com os itens do
    portão 4 quando o motivo é `com-erros`. Em seguida reinvocar `Modo: revisar`, do portão 1. A ajuda de
    descrição também é oferecida **uma vez por execução**: `PENDENTE-DESCRICAO` de novo vira `REPROVADO`
    com os erros que sobraram, sem `blocked`.

## Restrições

- Nunca editar o recurso aqui. Só o agent escreve, e só nos modos `completar-frontmatter` e
  `escrever-descricao`, depois do "sim" do Creator. As únicas escritas deste comando são as do status:
  `status.py set`, para os valores do Creator, e `review.py --registrar`, para o `reviewed`.
- Nunca gravar `reviewed` por outro caminho que o `review.py --registrar`, e só depois do `REVISADO` do
  agent. O `status.py set` recusa o valor: `reviewed` registra que a revisão passou, e o Creator não o
  declara.
- Nunca publicar, e nunca chamar `publish`, `get_resource` ou `submission_status`. A revisão não consulta
  o estado do recurso no Hub; a única chamada de rede é a tool `me` do servidor MCP `amflow-builder`, que
  o agent faz em `completar-frontmatter` para ler o id do autor.
- Nunca gravar `blocked` sem o Creator ter recusado a ajuda, e nunca sem `--motivo`.
- Um recurso por execução — para revisar outro, executar de novo.

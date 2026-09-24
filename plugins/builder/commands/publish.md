---
# about
name: publish
type: command
project: AmFlow
description: Envia ao Hub AmFlow um recurso skill ou agent já revisado (status reviewed), exatamente como o /amflow-builder:review o entregou, e grava local só o que o Hub aceitou
tags: [publish, submission, hub, creator, mcp, review]

# history
author: Bortoli
created: 2026-06-14
status: stable
version: 3.2.0
updated: 2026-09-24

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0

# claude-code
argument-hint: "[--price <centavos>]"
---

# /amflow-builder:publish

Envia ao Hub um recurso `skill` ou `agent` que já saiu `reviewed` do `/amflow-builder:review`. Não
revisa, não escaneia, não gera diff: o `review` já mediu o recurso, e este comando envia exatamente
o que ele aprovou. Usa a tool `publish` do servidor MCP `amflow-builder` (declarada em `.mcp.json`)
pelo agent `resource-publisher`, invocado uma vez, depois da confirmação do Creator — sem
`curl`/Bash de rede, sem token no contexto do modelo.

## Quando usar

- "publica a skill deep-research"
- "envia o agent reviewer pro Hub"

## Quando não usar

- "revisa a skill deep-research antes de eu publicar" — é `/amflow-builder:review`; este comando
  não aceita recurso que não seja `reviewed`
- "qual o status da minha submissão?" — é `/amflow-builder:publish-status`

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → sessão válida; prossiga. Com sessão já ativa, o `me` responde direto sem novo login.
- Sem sessão / erro → o conector `amflow-builder` não está autorizado nesta sessão. **Encerre
  aqui** — não rode `publish.py` nem invoque o agent. Oriente o usuário a autorizar o conector via
  `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

## Fase 1 — Listar recursos revisados

1. Resolver o projeto — `$CLAUDE_PROJECT_DIR` quando definido; senão, o diretório de trabalho
   atual. É o `<projeto>` de todo comando abaixo, sempre como caminho absoluto.

2. Chamar o script, nunca reimplementar a varredura:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" list <projeto> --status reviewed
   ```

   `reviewed` só é gravado pelo `/amflow-builder:review`, e só sobre `skill` e `agent` — a listagem
   nunca traz outro tipo. Um item marcado `[sem secure-invite]` na tabela não tem o arquivo do
   secure-invite ao lado do manifesto — a conferência da Fase 2 barra esse item ao ser escolhido.

3. Ler a saída:

   | Saída | O que fazer |
   |---|---|
   | Código 0, com tabela | Reproduzir a tabela tal como veio |
   | Código 0, sem tabela (lista vazia) | Encerrar: **"Nenhum recurso revisado para publicar. Retome com `/amflow-builder:status`, suba a versão se for uma atualização, e rode `/amflow-builder:review` — publicar exige `reviewed`."** |
   | Código 1 | Alguma linha começa com `ERRO` — exibir junto da tabela, não esconder |

## Fase 2 — Escolher o recurso

4. Perguntar ao Creator qual item publicar — por tipo/nome, ou pela linha. **Um recurso por
   execução**, nunca publicar a lista inteira em lote.

5. Item ambíguo ou fora da tabela → mostrar a tabela de novo e perguntar. Nunca adivinhar.

6. **Cópia duplicada.** Se o mesmo `tipo`/`nome` aparece em duas linhas, uma com `Local` sob
   `.claude/` e outra sem, usar a da pasta de desenvolvimento (a sem `.claude/`) e avisar em uma
   linha que há cópia em uso em `.claude/` — é a cópia que a revisão leu (mesma regra do `review`,
   D11 do plano `rebuild-resource-reviewer`). Existindo só a cópia em `.claude/`, seguir nela.

7. **O caminho do manifesto** é a coluna `Local` da linha escolhida, relativo ao `<projeto>` — é
   ele que vai para `publish.py` e para o agent.

8. **Conferência cedo (camadas 1 e 2), logo depois da escolha.** Antes de seguir para a Fase 3,
   rodar:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/publish.py" <projeto> <local> --conferir
   ```

   | Saída | O que fazer |
   |---|---|
   | `RESULTADO: OK` | Seguir para a Fase 3 |
   | `RESULTADO: BARRADO` | **Encerrar aqui** — exibir o `MOTIVO` tal como veio, sem reescrever, e orientar a rodar `/amflow-builder:review` para revisar (ou revisar de novo) o recurso. Nada foi enviado |

   Barrar aqui evita rodar as Fases 3 a 6 (versão, preço, changelog, prévia e confirmação M10) sobre
   um recurso que não vai publicar.

## Fase 3 — Ler o recurso

9. Ler o manifesto com `Read`. O campo muda de lugar por tipo:

   | Dado | `skill` | `agent` |
   |---|---|---|
   | versão | `metadata.amflow-version` | `version` |
   | identificador no Hub | `metadata.amflow-hub-id` | `hub_id` |
   | dependências | `metadata.amflow-dependencies` | `dependencies` |

   Dependências são uma string separada por espaço, cada entrada `tipo/nome@versão`
   (`check.py`, R-11); vazia ou ausente é "sem dependências".

## Fase 4 — Cenário e condições do envio

**Cenário A** (novo recurso): identificador do Hub ausente ou vazio → avançar direto para a Fase
5.

**Cenário B** (atualização): identificador presente e não vazio.

10. (Cenário B) Chame `submission_status({ hub_id: "<hub_id>" })`:

   `status: pending_review` → encerrar: **"`<tipo>/<nome>` já tem uma submissão aguardando
   revisão. Aguarde a resolução antes de submeter uma atualização."**

11. (Cenário B) Chame `get_resource({ type: "<tipo>", name: "<nome>" })`:

    Sem `current_version` (recurso ainda sem versão aprovada) → exibir aviso **"`<nome>` ainda não
    tem versão aprovada em prod — enviando como submissão completa."** e pular a checagem de
    versão abaixo.

    Com `current_version` → rodar a comparação por `publish.py`, determinística e testada
    (`scripts/tests/test_publish.py::TestVersaoSupera`, `TestChecarVersao`) em vez de comparar a
    string à mão — semver, não lexicográfico, então "1.10.0" supera "1.9.0":

    ```
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/publish.py" <projeto> <local> --versao-producao <current_version>
    ```

    `RESULTADO: OK` → segue. `RESULTADO: INSUFICIENTE` → encerrar com o `MOTIVO:` da saída.

    `get_resource` sem resposta (erro, timeout) → exibir aviso e seguir: a checagem local só
    antecipa a recusa, quem decide é o Hub.

12. (Cenário B, com dependências na Fase 3) Para cada `tipo/nome@versão`, chamar
    `get_resource({ type: "<tipo>", name: "<nome>" })`. Sem `current_version` → aviso **"a
    dependência `<tipo>/<nome>` ainda não está publicada."** Nunca bloqueia: é aviso, não condição
    de envio — o Hub decide na hora de instalar.

## Fase 5 — Preço e changelog

13. Preço, sempre mostrado e confirmado — nunca assumido:

    | Situação | Preço exibido como padrão |
    |---|---|
    | `--price <centavos>` na invocação | esse valor |
    | Cenário A | gratuito (`0`) |
    | Cenário B, com `current_version` | o `price` que `get_resource` devolveu na Fase 4 |
    | Cenário B, sem `current_version` | gratuito (`0`), mesma linha do Cenário A |

    Perguntar **"Confirmar"** ou **"Editar"**. Em Cenário B, o default nunca é gratuito por
    omissão: assumir `0` zeraria um recurso pago sem aviso.

14. (Cenário B) Solicitar `changelog`: **"Descreva brevemente o que mudou em relação à versão em
    produção."** Campo obrigatório; vazio encerra com: **"Changelog é obrigatório para
    atualizações."**

## Fase 6 — Prévia e confirmação

15. Exibir o resumo:

    ```
    Publicar <tipo>/<nome> v<versão> (<Cenário A: novo recurso | Cenário B: atualização>)
    Preço: <gratuito | R$ X,YZ (<centavos> centavos)>
    Changelog: <texto>          (só Cenário B)
    ```

    Sem diff e sem escolha de seções: o que foi revisado é o que vai, por inteiro (decisão 5 e 7
    do plano `publish-reviewed-only`).

16. **Confirmação humana (M10) — obrigatória, antes de invocar o agent.** Perguntar
    **"Confirmar"** / **"Cancelar"**. Cancelar encerra sem publicar. É a única confirmação deste
    fluxo.

## Fase 7 — Envio

17. Depois da confirmação, invoque o agent com o identificador **registrado**, que carrega o nome
    da pasta do agent:

    ```
    Agent(
      subagent_type: "amflow-builder:resource-publisher:resource-publisher",
      run_in_background: false,
      prompt: "Modo: publicar\nProjeto: <projeto>\nLocal: <caminho do manifesto>\nHubId: <hub_id ou vazio>\nType: <tipo>\nName: <nome>\nVersion: <versão>\nChangelog: <texto, só Cenário B>\nVisibility: public\nPrice: <centavos>"
    )
    ```

    O `run_in_background: false` pede o relatório na própria chamada, mas nem sempre vale: o
    `Agent` pode lançar o agent em segundo plano mesmo assim. Se a resposta da chamada disser que
    ele foi lançado em segundo plano, o relatório chega depois, como mensagem do subagente. Então
    **esperar**: no máximo uma linha dizendo que o envio está em andamento, sem adivinhar o
    resultado. Quando ele chegar, tratá-lo como o retorno da chamada.

18. Ler a linha `RESULTADO:` do relatório:

    | `RESULTADO` | O que fazer |
    |---|---|
    | `PUBLICADO` | O agent já gravou `amflow-hub-id` (na 1ª submissão) e `amflow-status: pending_review` local, pelo `publish.py --registrar`. Exibir o `SUBMISSION_ID` e a mensagem de recurso aguardando revisão do Manager. Sugerir `/amflow-builder:publish-status` para acompanhar |
    | `BARRADO` | A camada 1 ou a camada 2 deixou de bater entre a listagem e o envio (edição concorrente, por exemplo) — a mesma checagem da conferência cedo (Fase 2). Exibir o `MOTIVO` tal como veio, sem reescrever, e orientar a rodar `/amflow-builder:review` de novo — nada foi enviado |
    | `ERRO` | O Hub recusou. Exibir a mensagem tal como veio — nada foi gravado local |
    | `PUBLICADO-SEM-REGISTRO` | O Hub aceitou, mas a gravação local falhou. Exibir a mensagem de erro e avisar: **"O Hub já tem a submissão, mas o arquivo local não foi atualizado. Rode `/amflow-builder:publish-status` antes de tentar publicar de novo — não repita o envio sem conferir."** |
    | `NEGADO` | O Hub negou a publicação — a entry validation recusou o envio. Exibir a mensagem tal como veio e dizer que o recurso ficou `denied`; é preciso corrigir o que a mensagem aponta e rodar `/amflow-builder:review` de novo antes de tentar publicar |

## Restrições

- Nunca exibir tokens ao usuário.
- Nunca editar o arquivo local por conta própria — quem grava é o agent, pelo `publish.py
  --registrar`, e só depois do aceite do Hub.
- Nunca chamar a tool `publish` diretamente deste comando: é o agent quem chama, com
  `confirm: true` só depois do M10.
- Nunca publicar um recurso fora de `reviewed` — a Fase 1 já filtra, e o script reconfere na Fase
  7 mesmo assim.
- Um recurso por execução.

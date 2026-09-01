---
# about
name: publish
type: command
project: AmFlow
description: Valida, revisa e publica um recurso no Hub AmFlow — scanner de segurança, diff, submissão via MCP e atualização local do frontmatter
tags: [publish, submission, hub, creator, mcp]

# history
author: Bortoli
created: 2026-06-14
status: stable
version: 2.0.0
updated: 2026-07-11

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0

# claude-code
argument-hint: "[--validate-only] [--price <centavos>]"
---

# /amflow-builder:publish

Normaliza e publica um recurso do projeto no Hub. Tipos suportados: `skill`, `agent`, `hook`, `command`. Com `--validate-only`, executa apenas as Fases 1 e 2 e encerra sem publicar. Usa a tool `publish` do servidor MCP `amflow-builder` (declarada em `.mcp.json`) — sem `curl`/Bash, sem token no contexto do modelo.

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `me` do servidor MCP `amflow-builder`.

- Sucesso → sessão válida; prossiga. Com sessão já ativa, o `me` responde direto sem novo login.
- Sem sessão / erro → o conector `amflow-builder` não está autorizado nesta sessão. **Encerre aqui** — não execute o scan nem chame a tool `publish`. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

## Fase 1 — Identificar o recurso

1. Verificar `.claude/CLAUDE.md` no diretório atual — encerrar com erro se ausente.

2. Escanear o projeto e exibir lista numerada agrupada por tipo:

   ```
   skill:
     1. ultrareview
     2. code-diff-check
   agent:
     3. frontend-reviewer
   ```

   Encerrar se nenhum recurso publicável encontrado: **"Nenhum recurso publicável encontrado. Crie um com /amflow-builder:build."**

3. O Creator escolhe o recurso. Derivar `type` e `name` da seleção — não do frontmatter, ele já não é
   exigido lá (passo 4). Ler o arquivo do recurso com Read para obter o frontmatter completo.

   **Onde cada campo vive, por tipo.** Para `skill`, seis campos saíram do topo e foram para
   `metadata` (norma em `scripts/frontmatter/skill-frontmatter.md`, no repositório AmFlow):
   `version` → `amflow-version`, `status` → `amflow-status`, `author` → `amflow-author`, `tags` →
   `amflow-tags` (separadas por espaço, nunca lista), `dependencies` → `amflow-dependencies`,
   `hub_id` → `amflow-hub-id`. `source` não existe em nenhum momento na fonte — só na cópia
   instalada, nunca no repositório do Creator. Todo passo abaixo que cite um desses campos para uma
   skill lê e escreve em `metadata`. Para `agent`, `hook` e `command`, nenhum campo muda de lugar.

## Fase 2 — Validação e Revisão

4. Validação silenciosa:
   - Encerrar se ausentes: `name`, `version`.
   - Exibir aviso (não bloqueia) se `author` ausente.
   - Para `skill`: encerrar se `evals/eval_queries.json` estiver ausente, intocado (`skill_name` ainda
     `skill-name`, ou `description_under_test` vazio) ou sem nenhum caso `should_trigger: false` que
     não seja o texto do template — **"Evals não preenchidos: `<caminho>` — declare ao menos um
     near-miss antes de publicar."**

     A `description` é a única superfície de ativação de uma skill, e o near-miss é o que expõe uma
     descrição larga demais. Nada aqui executa as queries: o gate é sobre declará-las.

5. Exibir sequencialmente os campos para revisão. Para cada um, perguntar **"Confirmar"** ou **"Editar"**:

   | Step | Preamble | Editar vai para |
   |---|---|---|
   | `revisao_categoria` | "Categoria atual: <d1> / <d2>" | survey d1 → d2 → retorna aqui |
   | `revisao_output` | "Output atual: <d4>" | lista de 6 tipos → retorna aqui |
   | `revisao_tags` | "Tags atuais: <tags>" | checkbox com 3 sugestões → retorna aqui |
   | `revisao_descricao` | "Descrição atual: <description>" | survey intencao → loop → retorna aqui |
   | `revisao_price` | "Preço: gratuito" ou "Preço: <valor> (centavos)" — ver o default abaixo | perguntar valor em centavos → retorna aqui |

   `skill`: pular `revisao_categoria` e `revisao_output` — `d1`/`d2`/`d4` saíram do frontmatter da
   norma nova e não têm mais onde escrever. Continuam existindo só como conversa do survey de criação
   (`/amflow-builder:build`), não como campo a revisar aqui.
   Hooks: `d1`/`d2` são omitidos; `d4` fixo como `action` — exibir apenas: `"Output (fixo para hooks): action"` com somente "Confirmar".
   Workflow agents (`tags` contém `workflow`): pular `revisao_categoria` e `revisao_output`.

   **O default de `revisao_price`**, e ele não é sempre gratuito:

   | Situação | Preço exibido como padrão |
   |---|---|
   | `--price <centavos>` na invocação | esse valor, e o step é pulado |
   | Sem a flag, Cenário A | gratuito (`0`) |
   | Sem a flag, Cenário B | o `price` que `get_resource` devolve no passo 10 |

   Em Cenário B o default **não** é gratuito. O preço saiu do frontmatter, e oferecer `0` como padrão
   numa republicação faria de "Confirmar" o caminho que zera um recurso pago — sem erro e sem aviso,
   que é exatamente o que esta correção existe para fechar. Cenário B sem `current_version` (o aviso
   do passo 10) cai na linha do Cenário A.

   A flag existe para o fluxo autônomo: o agent `publisher` pula os prompts editoriais desta fase, e
   sem ela não teria como declarar preço nenhum.

6. (Cenário B apenas — `hub_id` presente e não vazio) Solicitar `changelog`:
   > "Descreva brevemente o que mudou em relação à versão em produção."
   Campo obrigatório; vazio encerra com: **"Changelog é obrigatório para atualizações."**

7. Se `--validate-only` → exibir **"Validação concluída."** e encerrar.

## Fase 3 — Scanner de segurança

8. Escanear o **corpo** do recurso (excluindo frontmatter):

   | Categoria | Padrões bloqueados |
   |---|---|
   | Prompt injection | `ignore previous instructions`, `override all instructions`, `esquece`, `forget` |
   | Comandos shell | `curl`, `wget`, `netcat`, `nc`, `bash -c` (exceção: `hook.sh` — não aplicar esta categoria) |
   | Paths absolutos | `~/`, `/Users/`, `/home/`, `%APPDATA%`, `$HOME`, `$PATH`, `$SSH` |
   | Dados suspeitos | Strings Base64 com 60+ caracteres |

   Detecção → encerrar: **"Publicação bloqueada pelo scanner de segurança. Remova os padrões listados."** (checagem client-side, rápida — o Hub roda a mesma classe de verificação server-side na tool, independentemente).

## Fase 4 — Seleção por Cenário

**Cenário A** (novo recurso): `source: local` / vazio / ausente, **ou** `source: hub/...` com `hub_id` vazio → avançar direto para Fase 5.

**Cenário B** (atualização): `source: hub/...` **e** `hub_id` presente e não vazio.

Para `skill`, `source` não entra no critério — nunca existe na fonte, publicada ou não. É só
`amflow-hub-id`: ausente ou vazio → Cenário A; presente e não vazio → Cenário B.

9. (Cenário B) Chame a tool `submission_status({ hub_id: "<hub_id>" })`:

   `status: pending_review` → encerrar: **"<nome> já tem uma submissão aguardando revisão. Aguarde a resolução antes de submeter uma atualização."**

10. (Cenário B) Buscar versão em produção via `get_resource({ type: "<tipo>", name: "<nome>" })`:

    Sem `current_version` (recurso ainda não publicado) → exibir aviso **"<nome> ainda não tem versão aprovada em prod — submetendo versão completa."** e avançar para Fase 5 pulando [11] e [12].

11. (Cenário B) Gerar diff entre local stripado e versão prod:
    - Markdown (`skill`, `agent`, `command`): comparar seção a seção por heading H2 + frontmatter como seção
    - JSON (`hook`): comparar campo a campo (top-level)
    - Nenhuma diferença → perguntar: **"Nenhuma alteração detectada em relação à versão em produção. Deseja prosseguir mesmo assim?"** Não → encerrar.

12. (Cenário B) Exibir diff completo e checkbox de seções alteradas:
    > "Quais seções incluir na atualização?"
    Seleção vazia → encerrar sem publicar.

## Fase 5 — Publicação

13. Stripping do conteúdo a publicar (nunca modificar o arquivo local):
    - `skill`: remover `metadata.amflow-hub-id`, se presente — o bundle não carrega hub_id. Nada mais
      a remover do frontmatter: `type`/`project`/`source` já não estão lá pra remover
    - Demais tipos: remover do frontmatter `project`, `source`, `hub_id`
    - Remover do corpo: paths absolutos (`~/`, `/Users/<user>/`, `/home/<user>/`) e ocorrências literais do nome do projeto
    - (Cenário B) Substituir seções não-selecionadas em [12] pelo conteúdo prod correspondente

14. (Cenário B) Version bump:
    - `local == prod` → bump automático: `prod + 1 patch`
    - `local > prod` → respeitar versão local (bump manual do Creator)
    - `local < prod` → encerre: **"Versão local (<local>) é anterior à versão em prod (<prod>). Atualize o frontmatter antes de publicar."**

    Houve bump em `skill` ou `agent` → atualizar a linha `Versão X.Y.Z` do `[tipo]-description.md` **na cópia a publicar**, para a versão submetida. O Hub compara as duas e recusa o bundle quando divergem.

15. Exibir preview do conteúdo limpo. Cenário B: exibir também o resumo das seções incluídas.

16. **Confirmação humana (M10) — obrigatória, antes de chamar a tool.** Perguntar **"Confirmar"** / **"Cancelar"**. A tool `publish` muta dados reais no Hub no instante em que é chamada — a confirmação precisa acontecer ANTES da chamada, não depois. Cancelar encerra sem publicar.

17. Após a confirmação, chame a tool `publish`:

    ```
    publish({
      hub_id: "<hub_id>",       // presente apenas no Cenário B
      name: "<nome>",
      type: "<tipo>",
      version: "<versão>",
      changelog: "<texto>",     // ausente no Cenário A
      visibility: "<public|exclusive>",
      assigned_to: "<uuid>",    // presente apenas quando visibility: exclusive
      price: <centavos>,        // decidido em revisao_price (passo 5) ou por --price — nunca lido do frontmatter
      files: [{ path: "<arquivo>", content: "<conteúdo>" }],
      confirm: true             // só true depois do passo 16 — nunca antes
    })
    ```

    Arquivos por tipo — cada `path` espelha o layout do recurso em disco, sob `.claude/`:
    - `skill` → `SKILL.md` + `skill-description.md`
    - `agent` → `<nome>.md` + `agent-description.md` (+ `<nome>-workflow.mmd` se existir, para workflow agents)
    - `hook` → `hook.json` + `hook.sh`
    - `command` → `command.md`

    O `[tipo]-description.md` é **obrigatório** para `skill` e `agent`: o Hub recusa o bundle sem ele, e recusa também quando a versão declarada nele diverge da versão submetida. `hook` e `command` ainda não entram na norma.

18. Tratar resposta:
    - Sucesso → `{ hub_id, submission_id, status: "pending_review" }`. Exibir `submission_id`.
    - Erro → exibir a mensagem retornada pela tool (inclui detalhe de validação quando o bundle é rejeitado).

## Fase 6 — Atualização local

19. Atualizar o arquivo local com a ferramenta Edit (apenas os campos alterados):

    | Campo | Novo valor |
    |---|---|
    | `hub_id` | uuid retornado — gravar apenas na primeira submissão; se já existia, manter sem alteração |
    | `version` | versão submetida (após bump) |
    | `source` | `hub/<tipo>/<nome>@<versão>` |
    | `status` | `pending_review` em `skill`; `published` nos demais tipos |

    Para `skill`, os três primeiros vivem em `metadata` (`amflow-hub-id`, `amflow-version`,
    `amflow-status`) — **`source` fica de fora**: a norma reserva `amflow-source` só pra cópia
    instalada, nunca escrever na fonte. Nos demais tipos, os quatro seguem no topo, sem mudança.

    **`pending_review`, não `published`, em `skill`.** Submeter não publica: a submissão entra na fila
    do Manager. Na norma, `published` é escrito pelo `/amflow-builder:publish-status`, quando o Hub
    aprova — e é ele quem move o estado dali em diante. Os demais tipos mantêm `published`: o domínio
    de `status` deles não tem `pending_review`.

    Arquivo por tipo: `skill` → `SKILL.md` | `agent` → `<nome>.md` | `hook` → `hook.json` | `command` → `command.md`

    Em `skill` e `agent`, atualizar também a linha `Versão X.Y.Z` do `[tipo]-description.md` local para a versão submetida — o arquivo não tem frontmatter, e é essa linha que o gate compara na próxima publicação.

20. Exibir sumário: `submission_id` e mensagem de recurso aguardando revisão do Manager.

## Restrições

- Nunca exibir tokens ao usuário.
- Stripping apenas na cópia enviada ao Hub — o arquivo local nunca é modificado pelo stripping.
- Usar Edit para atualizar frontmatter local — nunca sobrescrever o arquivo inteiro.
- Um recurso por execução.
- Nunca chamar a tool `publish` com `confirm: true` antes de completar o passo 16.

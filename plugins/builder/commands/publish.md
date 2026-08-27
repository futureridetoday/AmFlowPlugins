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
version: 2.1.0
updated: 2026-08-27

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
- Sem sessão / erro → o conector `amflow` não está autorizado nesta sessão. **Encerre aqui** — não execute o scan nem chame a tool `publish`. Oriente o usuário a autorizar o conector via `/mcp` (ou no install do plugin) e reexecutar.

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

3. O Creator escolhe o recurso. Derivar `type` e `name` da seleção. Ler o arquivo do recurso com Read para obter o frontmatter completo.

   **Onde cada dado mora, por tipo.** `skill` segue norma própria — `scripts/frontmatter/skill-frontmatter.md`, no repositório AmFlow: o dado do AmFlow vive no bloco `metadata`, com prefixo `amflow-`. Os outros três seguem a tabela do `.claude/CLAUDE.md`, com os campos no topo.

   | Dado | `skill` | `agent`, `hook`, `command` |
   |---|---|---|
   | versão | `metadata.amflow-version` | `version` |
   | estado | `metadata.amflow-status` | `status` |
   | autor | `metadata.amflow-author` | `author` |
   | tags | `metadata.amflow-tags` — string separada por espaço | `tags` — lista YAML |
   | identificador no Hub | `metadata.amflow-hub-id` | `hub_id` |
   | origem | — não existe na fonte | `source` |

   Onde este comando disser "a versão", "o estado", "as tags" ou "o identificador do Hub", ler pela coluna do tipo selecionado.

## Fase 2 — Validação e Revisão

4. Validação silenciosa:
   - Encerrar se ausentes: `name` e a versão.
   - Exibir aviso (não bloqueia) se o autor ausente.

   `type` não entra na checagem: ele vem da seleção em [3], não do arquivo. Exigi-lo presente no
   frontmatter era exigir que o recurso repetisse o que a pasta já diz.

5. Exibir sequencialmente os campos para revisão. Para cada um, perguntar **"Confirmar"** ou **"Editar"**:

   | Step | Preamble | Editar vai para |
   |---|---|---|
   | `revisao_tags` | "Tags atuais: <tags>" | checkbox com 3 sugestões → retorna aqui |
   | `revisao_descricao` | "Descrição atual: <description>" | survey intencao → loop → retorna aqui |

   As tags saem do campo de tags do tipo — ver a tabela em [3]. Em `skill`, editar grava de volta em
   `metadata.amflow-tags`, separadas por espaço.

   **`d1`, `d2` e `d4` saíram da revisão.** Não são campos da norma de skill nem da tabela do
   `.claude/CLAUDE.md`, e nunca chegaram ao Hub — a tool `publish` não os recebe. Ficam pendentes de
   `B-05`, no backlog do AmFlow. Com eles saem os dois desvios que existiam só para contorná-los: a
   omissão em `hook` e o pulo em workflow agent, este último a única leitura de `tags` fora da
   revisão das próprias tags.

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

O que separa os dois é **o identificador do Hub** — ver a tabela em [3].

**Cenário A** (novo recurso): identificador do Hub ausente ou vazio → avançar direto para Fase 5.

**Cenário B** (atualização): identificador do Hub presente e não vazio.

Em `agent`, `hook` e `command` a origem (`source`) continua valendo como sinal de apoio: `source:
local` / vazio / ausente cai em A mesmo com `hub_id` preenchido. **Em `skill` a origem não serve de
discriminador** — a norma reserva `amflow-source` à cópia instalada, e a fonte no repositório do
Creator nunca a tem. Skill já publicada é reconhecida por `metadata.amflow-hub-id`, e só por ele;
exigir `source` ali classificaria toda atualização como recurso novo, pulando o gate de submissão
pendente, o diff, o changelog e o gate de versão.

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
    - `skill` → remover de `metadata`: `amflow-hub-id` e `amflow-source`. Não há `project` a remover — a norma de skill não tem esse campo
    - `agent`, `hook`, `command` → remover do frontmatter: `project`, `source`, `hub_id`
    - Remover do corpo: paths absolutos (`~/`, `/Users/<user>/`, `/home/<user>/`) e ocorrências literais do nome do projeto
    - (Cenário B) Substituir seções não-selecionadas em [12] pelo conteúdo prod correspondente

14. (Cenário B) Version bump:
    - `local == prod` → bump automático: `prod + 1 patch`
    - `local > prod` → respeitar versão local (bump manual do Creator)
    - `local < prod` → encerre: **"Versão local (<local>) é anterior à versão em prod (<prod>). Atualize o frontmatter antes de publicar."**

    Houve bump em `skill` ou `agent` → atualizar a linha `Versão X.Y.Z` do `[tipo]-description.md` **na cópia a publicar**, para a versão submetida. O Hub compara as duas e recusa o bundle quando divergem.

15. Exibir preview do conteúdo limpo, **com o preço a submeter**. Cenário B: exibir também o resumo das seções incluídas.

    **O preço**, em centavos, resolvido nesta ordem:

    | Situação | Valor |
    |---|---|
    | `--price <centavos>` na invocação | esse valor, sempre — vence as duas linhas abaixo |
    | Sem `--price`, Cenário A | `0` |
    | Sem `--price`, Cenário B | o `price` que `get_resource` devolveu em [10] |

    Cenário B sem `current_version` — o aviso de [10] — cai na linha do Cenário A: `0`.

    O preço deixou de morar no frontmatter. `submit.ts` sempre o leu do payload, nunca do arquivo, e
    era o único campo que mudava de significado entre submissões da mesma skill. **O default do
    Cenário B é a versão em produção, não `0`**: republicar um recurso pago sem passar `--price` o
    transformaria em gratuito, sem erro e sem aviso. Por isso o valor aparece no preview, antes da
    confirmação de [16] — preço é decisão do Creator, e decisão que ninguém vê não foi tomada.

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
      price: <centavos>,        // resolvido em [15]
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

    | Dado | Novo valor | Onde grava em `skill` | Onde grava nos outros três |
    |---|---|---|---|
    | identificador no Hub | uuid retornado — gravar apenas na primeira submissão; se já existia, manter sem alteração | `metadata.amflow-hub-id` | `hub_id` |
    | versão | versão submetida (após bump) | `metadata.amflow-version` | `version` |
    | estado | `pending_review` em `skill`; `published` nos outros três | `metadata.amflow-status` | `status` |
    | origem | `hub/<tipo>/<nome>@<versão>` | **não grava** | `source` |

    Arquivo por tipo: `skill` → `SKILL.md` | `agent` → `<nome>.md` | `hook` → `hook.json` | `command` → `command.md`

    **Gravar no lugar certo é o que mantém o recurso dentro da norma.** Em `skill`, os quatro dados
    vivem em `metadata`; escrevê-los no topo cria campo órfão e faz o verificador
    (`scripts/frontmatter/check.py`, no AmFlow) reprovar o arquivo que este comando acabou de tocar —
    a publicação desfaria a migração a cada submissão.

    **`pending_review`, não `published`.** Submeter não publica: a submissão entra na fila do Manager.
    Na norma de skill, `published` é escrito pelo `/amflow-builder:publish-status`, quando o Hub
    aprova. Os outros três tipos mantêm `published` — o domínio de `status` deles não tem
    `pending_review`.

    **`source` não é gravado em `skill`.** A norma reserva `amflow-source` à cópia instalada; na
    fonte, no repositório do Creator, a chave não existe. Nos outros três tipos, `source` continua
    recebendo `hub/<tipo>/<nome>@<versão>`.

    Em `skill` e `agent`, atualizar também a linha `Versão X.Y.Z` do `[tipo]-description.md` local para a versão submetida — o arquivo não tem frontmatter, e é essa linha que o gate compara na próxima publicação.

20. Exibir sumário: `submission_id` e mensagem de recurso aguardando revisão do Manager.

## Restrições

- Nunca exibir tokens ao usuário.
- Stripping apenas na cópia enviada ao Hub — o arquivo local nunca é modificado pelo stripping.
- Usar Edit para atualizar frontmatter local — nunca sobrescrever o arquivo inteiro.
- Um recurso por execução.
- Nunca chamar a tool `publish` com `confirm: true` antes de completar o passo 16.

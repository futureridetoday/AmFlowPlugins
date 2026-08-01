---
# about
name: modelo-dev-units
type: doc
project: AmFlow
description: Norma do modelo de Unidades de Desenvolvimento — hierarquia core/module/block/unit, unidade como arquivo autossuficiente para cold-start, estado derivado de verificação, norma de lote de 8 passos, avaliação de escopo e a skill dev-units. Documento normativo: define o formato que os planos obedecem
tags: [dev-units, metodologia, spec-driven, clean-architecture, core, cold-start, processo, documentacao, fix, plan]

# history
author: Bortoli
created: 2026-07-19
status: draft
version: 2.1.0
updated: 2026-07-24

# system
scope: project
auto_load: false
dependencies: []
---

# Modelo dev-units — norma

Define o método de **Unidades de Desenvolvimento** do AmFlow: hierarquia, formatos, nomenclatura,
gates de verificação e a skill que o executa.

> **Este documento é norma, não plano.** Não tem `plan_id`, não entra em `_planos.md`, e não segue o
> formato de plano — é o formato **que os planos obedecem**. A ordem importa: a norma existe
> primeiro, planos vêm depois e a seguem. Um documento que definisse o formato de plano *sendo* um
> plano nesse formato seria circular.
>
> A implementação desta norma é o plano
> [`0002-dev-units`](../builder/0002-dev-units/0002-dev-units.md) — o primeiro escrito sob ela.

**Por que existe:** o padrão anterior especificava bem, mas não fechava o ciclo. Não definia
"pronto", não ligava à verificação, não tinha estado, e não produzia unidades executáveis por um
agente sem contexto. O resultado medido: 18 de 18 documentos em `status: draft` com código em
produção.

---

## O gargalo que o modelo precisa resolver

O fluxo que hoje produz os melhores resultados é **planejar com Opus, desenvolver com Sonnet**. Mas
ele depende de um passo manual e repetido: pedir, a cada vez, que as tarefas do plano sejam
documentadas com informação suficiente para **cold-start** — execução por um agente que não
participou do planejamento.

O modelo transforma esse pedido manual em **output obrigatório** da derivação de unidades.

---

## Fundamentação — por que este modelo, e não outro

Ancorado em evidência empírica, não em tendência de mercado.

| Fonte | Dado | Implicação |
|---|---|---|
| **METR 2025** (RCT, 16 devs experientes, 246 tarefas) | Devs foram **19% mais lentos** com IA, mas estimaram ter sido **20% mais rápidos** | Percepção de progresso não é confiável. É preciso um **oráculo objetivo** |
| **DORA 2024** (~39 mil profissionais) | Adoção de IA acompanhada de **−1,5% throughput** e **−7,2% estabilidade**; causa apontada: o campo **esqueceu o small batch** | O gargalo é o **tamanho do lote**, não a ferramenta |
| **DORA 2025** (~5 mil profissionais) | "IA **amplifica** o que já existe"; **small batch amplifica os efeitos positivos** | Estrutura decide se a IA é ativo ou passivo |

**O que deliberadamente não foi adotado.** Spec-Driven Development (GitHub Spec Kit, AWS Kiro, Tessl)
é a corrente dominante, mas **nenhuma dessas ferramentas tem validação empírica**. A avaliação do
Spec Kit identificou incompatibilidade estrutural com o AmFlow: é **spec-first** (spec descartada
após uso) enquanto o AmFlow precisa de **spec-anchored**; tem baixo benefício relatado em sistemas
multi-módulo e brownfield; e produz **volume documental**, que é o modo de falha já vivido aqui.

Conclusão: adotar o **princípio** (spec-anchored, lote pequeno, verificação objetiva), não a
ferramenta.

---

## Diagnóstico medido — o padrão atual

Auditoria dos 18 arquivos `dev-units*.md` em `docs/mvp/20_delivery/`. **Este acervo não será migrado
agora** (ver *Estratégia de adoção*) — o diagnóstico justifica o desenho, não dimensiona retrabalho
imediato.

### O que funciona (preservar)

| Capacidade | Evidência |
|---|---|
| Fatia vertical como unidade | 86 unidades com contrato Entrada/Saída/Auth/Efeito/Erro |
| Rastreabilidade doc ↔ código | **90 referências** via comentário-cabeçalho (`hub/proxy.ts:5` → `// AU-06`) |
| Registro de pendências | **11 lacunas** `L-XX` catalogadas |
| Preservação do racional | Notas `>` com trade-offs (ex.: invalidação antecipada em `AU-02`) |

### O que falta

| Lacuna | Medição |
|---|---|
| **Não define "pronto"** | **0 de 18** contêm critério de aceite |
| **Não liga à verificação** | **0 de 18** declaram teste — apesar de existirem **18 arquivos de teste** |
| **Não tem estado** | **18 de 18** em `status: draft`, com código em produção |
| **Não norma o lote** | De **1 a 18** unidades por arquivo; **22 de 86 (26%)** sem sequência numerada |
| **Não serve a cold-start** | Nenhuma declara arquivos a tocar nem normas aplicáveis |

### Cobertura por core

| Core | dev-units |
|---|---|
| Hub | 17 |
| Worker | 1 |
| **Builder** | **0** |

O Builder é um core declarado, produz `plugins/builder`, e não tem nenhuma especificação.

---

## Conceitos estruturantes

### Plano e módulo são eixos diferentes

| | Plano | Módulo |
|---|---|---|
| Natureza | **Temporal** — um lote de trabalho aprovado | **Estrutural** — permanente |
| Densidade | Leve; não precisa ser denso | Denso — doc viva |
| Ciclo | Abre, executa, fecha | Nunca fecha, evolui |
| Contém | Backlog com as unidades | As unidades |

O plano nasce em `_inbox/`, passa por revisão e aprovação, e **é movido para a pasta que ele criou** —
tornando-se o registro permanente da intenção, ao lado das unidades que gerou.

### Cold-start é o critério de suficiência da unidade

> Uma unidade está completa quando um agente **sem nenhum contexto da conversa** consegue executá-la
> sem precisar perguntar nada.

Isso unifica o problema de origem: a variância do agente é variância por contexto insuficiente, e
cold-start é o caso extremo dessa condição. Uma unidade que sobrevive ao cold-start sobrevive a
qualquer contexto.

O teste é empírico e barato: **se o executor precisou perguntar, a unidade falhou** — e a correção é
da unidade, não do executor.

Campos exigidos:

| Campo | Estado no padrão atual |
|---|---|
| Contrato (Entrada/Saída/Auth/Efeito/Erro) | Existe |
| Sequência numerada (≤ 8 passos) | Falta em 26% |
| Dependências | Existe |
| **Arquivos a tocar** (caminhos concretos) | Não existe |
| **Normas aplicáveis** (referência, nunca cópia) | Implícito em `hub-front` |
| **Critério de aceite** | 0 de 18 |
| **Teste que o comprova** | 0 de 18 |

---

## Modelo proposto — cinco componentes

### 1. Hierarquia estrutural

```
System           → AmFlow
  Core           → fronteira de ownership: Security, Worker, Hub, Builder
    Module       → capability de domínio: auth, catalog, mcp
      Block      → variação/extensão aditiva (opcional): login-google
        Unit     → fatia vertical mínima verificável: AU-02
```

> **Vocabulário.** Os nomes acima são a forma canônica em **código, caminhos de pasta e frontmatter**
> (`core`, `module`, `block`, `unit`). **Na prosa, usa-se português** — sistema, core, módulo, bloco,
> unidade. Forçar o inglês no texto explicativo custa precisão sem ganho: *"as unidades de
> desenvolvimento concluídas hoje"* não tem equivalente natural em inglês.

> **`core` aqui não é o `core` de Clean Architecture.** No AmFlow é uma fronteira **vertical** (por
> ownership) — conceitualmente um **Bounded Context** do DDD. Em Clean Architecture, "core" designa o
> centro **concêntrico** de política, oposto às bordas. O Core Hub tem, ele próprio, um core
> concêntrico (regras do marketplace) e bordas (Next.js, Supabase, Stripe). O princípio de Clean
> Architecture que este modelo adota é a **regra de dependência** (componente 3), não a nomenclatura.

**Ownership e localização são eixos independentes.** Um core pode possuir um módulo hospedado em
outro core, por necessidade arquitetural:

| | Security | Hub |
|---|---|---|
| Produz deployable | Não | Sim |
| É dono de `auth` | **Sim** | Não |
| Hospeda `auth` | Não | **Sim** |

O módulo de autenticação fica em `hub/auth/` porque o Hub é o Identity Provider onde o Supabase Auth
roda; o módulo declara `owner: security` no frontmatter.

**Estrutura no disco — `docs/plan/`:**

```
docs/plan/
  _inbox/                     planos aguardando revisão e aprovação
  _planos.md                  tabela dos planos aprovados — fonte da numeração

  security/                   core transversal — sem deployable próprio
    index.md
    system/                   normativa de segurança, vale para todos os cores

  hub/
    index.md                  doc geral do core, na raiz
    system/                   arquitetura, testes, ferramentas, infra do Hub
    0001-mcp/                 módulo — a pasta recebe o número do plano que a criou
      0001-mcp.md             plano — mesmo nome da pasta
      index.md                doc geral do módulo
      01-handler-auth.md      unidade — numeração por plano
      02-search-catalog.md
      0005-oauth/             bloco — numerado pelo plano que o criou
        0005-oauth.md
        01-callback.md
      fix/                    opcional
    0002-auth/                owner: security · hospedado no hub
    0003-catalog/

  worker/    index.md · system/
  builder/   index.md · system/
```

- **`system/`** guarda o que **não é feature** mas é fundamental ao core: definições de arquitetura,
  testes, ferramentas, infra. É onde vive a camada normativa do core (componente 3).
- **Bloco e `fix` são opcionais** — módulo simples guarda unidades direto na raiz.
- **Doc geral fica na raiz** do core e do módulo.

**Grão decidido:** bloco é **pasta**; unidade é **arquivo**. O arquivo por unidade é exigência do
cold-start — o executor recebe "leia este arquivo e execute", sem precisar extrair uma seção de um
documento de 500 linhas.

### 2. Estado derivado de verificação

A unidade não é dois artefatos (plano, depois documentação). É **um artefato com fases de vida**:

| Fase | O que a unidade é | Estado |
|---|---|---|
| Antes | Prescritiva — contrato a cumprir | `spec` |
| Durante | Contrato em execução | `wip` |
| Depois | **Descritiva — o que está verificado em produção** | `verified` |

**A transição não é editada à mão. É o teste passar.** Estado declarado manualmente é o que corrompe
— os 18/18 `draft` com código em produção são a prova.

Consequência: uma unidade `verified` cujo teste quebra **volta automaticamente a divergente**. A
documentação fica impedida de mentir em silêncio.

**Como o estado é computado:** a **unidade declara seu teste**; um script lê a declaração, roda o
alvo e deriva o estado. Direção `spec → teste`, nunca o inverso.

Evidência que fixou a direção: a suíte atual tem apenas **4 referências** a identificadores de
unidade (`auth.test.ts:46` → AU-10, `licenses.test.ts:203` → LI-05, `connect.test.ts:22` → AU-01,
`reviews.test.ts:271` → RE-04), e os `describe()` são nomeados por função (`getCart`, `normalize`).
Exigir que o teste declare a unidade obrigaria a reescrever 18 arquivos, com benefício idêntico.

Granularidade inicial: **arquivo de teste**. Aceita-se a imprecisão — uma unidade pode ficar
não-verificada por falha de outra no mesmo arquivo — em troca de custo zero sobre a suíte existente.
Refina-se para bloco de teste (`vitest -t`) conforme testes novos forem escritos.

**Duas projeções, uma fonte.** O resultado é projetado no arquivo da unidade **e** no backlog do
arquivo do plano. Nunca são duas declarações independentes — por isso não divergem.

### 3. Camada normativa — princípios, guidelines, guardrails, referências

Vive em **`<core>/system/`**.

| Elemento | O que é | Exemplo |
|---|---|---|
| **Princípio** | direção, o porquê — estável | mobile first |
| **Guideline** | como técnico | breakpoints, biblioteca de UI |
| **Guardrail** | limite verificável | nunca `process.env` direto |
| **Referência** | fonte externa canônica | docs do Supabase SSR |

**Regra anti-drift inegociável: uma fonte por fato.** A unidade *referencia* a norma, nunca a copia.

O `CLAUDE.md` permanece como camada normativa de **processo**; `<core>/system/` cobre o **domínio**;
`security/system/` cobre o que é **transversal** a todos os cores.

#### Guardrail fundador — regra de dependência entre cores

É o que dá função arquitetural ao nível core, e a tradução real do princípio central de Clean
Architecture (*Dependency Rule*):

```
Worker  ──► Hub
Builder ──► Hub
Hub     ──► (nenhum core)
```

**Já é respeitado pelo código hoje** — verificado em 2026-07-19:

| Direção | Medição |
|---|---|
| Hub → plugins | **0 referências** |
| plugins → Hub | múltiplas (`worker/.mcp.json`, `plugin.json`, `commands/{get,hub-check,hub-update}.md`) |

Declarar não é aspiração: formaliza um invariante que já vale. Por ser **verificável por grep**, é o
candidato natural a primeiro guardrail automatizado.

### 4. Norma de lote e decomposição

- **Teto:** **8 passos de sequência por unidade**. Acima disso, a unidade divide-se.
- **Revisão de plano:** avalia contra a norma e **sugere os blocos**.
- **Decomposição:** informa se o trabalho vira **fases**, e cada fase em **unidades**.

O teto é o **p90 das 86 unidades existentes**, não arbítrio:

| Métrica | Passos |
|---|---|
| p50 | 5 |
| p75 | 6 |
| **p90 — teto adotado** | **8** |
| máximo atual | 15 (`PU-00`, `FE-11`) |

Marcaria 8 unidades como acima da norma — cerca de 9%, suficiente para o gate ter efeito sem travar
o fluxo.

Por que passos, e não linhas ou arquivos: é a única métrica **mensurável antes de implementar**.
Linhas de código só se conhecem depois, e gate corretivo não previne. Passos também correlacionam
com o número de decisões que o agente precisa tomar — a origem da variância.

**Unidade sem sequência é incompleta, não isenta.**

### 5. Preservação do que funciona

- **Comentário-cabeçalho** de rastreabilidade (90 refs) → formalizar como obrigatório.
- **Lacunas `L-XX`** (11 catalogadas) → manter.
- **Racional nas notas `>`** → promover a **ADR leve**, preservando o *porquê* sem inchar o documento.

> **Sobre o índice:** versões anteriores desta proposta previam um "índice vivo" como componente
> próprio. Ele foi **eliminado** — com a hierarquia de pastas no disco, o índice viraria uma terceira
> projeção do mesmo fato, e redundância é drift. A navegação passa a vir da própria estrutura; o
> estado de um trabalho, do backlog no arquivo do plano; e a visão agregada por core, de **consulta sob
> demanda** (script que varre e reporta), nunca de arquivo persistido que desatualiza.

---

## Formato do arquivo de unidade

Referência viva:
[`docs/plan/hub/0001-mcp/01-handler-auth.md`](../hub/0001-mcp/01-handler-auth.md) — instância
real, validada contra código em produção. O formato **não é duplicado aqui**: o exemplo é a fonte.

### Regiões — quem escreve o quê

Esta é a regra que torna o estado projetável sem risco de perda:

| Região | Quem escreve | Conteúdo |
|---|---|---|
| **Frontmatter** | Script (bloco `# verificação`) e humano (demais) | `state`, `test`, `verified_at` são do script |
| **Corpo** | Humano / skill | Contrato, sequência, arquivos, normas, critério de aceite |

O script **nunca edita o corpo**. Escreve apenas três campos do frontmatter — região delimitada,
parseável e sem prosa. O mesmo princípio se aplica ao backlog no arquivo do plano, cujo formato é o
próximo item a definir.

### Blocos do corpo

| Bloco | Função |
|---|---|
| Responsabilidade | Uma frase — o que faz e por que existe |
| Contrato | Entrada · Saída · Auth · Efeito · Erro |
| Sequência | Passos numerados, **teto de 8** |
| Arquivos | Caminhos concretos com `arquivo:linha` — exigência do cold-start |
| Dependências | O que precisa existir antes |
| Normas aplicáveis | Tabela de **referências**, nunca cópia |
| Critério de aceite | Uma frase verificável |
| Verificação | Teste, comando para rodá-lo, último resultado |
| Fonte | De onde veio a spec |

### Identificador

O `unit_id` combina o número do plano com o número da unidade dentro dele:

```yaml
unit_id: 0001-02        # plano 0001, segunda unidade
```

A numeração das unidades é **por plano** — recomeça em `01` a cada plano novo. Quatro dígitos para o
plano, dois para a unidade.

### Tipo de unidade

Nem toda unidade entrega código. O campo `unit_type` define o que ela produz e qual é seu oráculo:

```yaml
unit_type: dev     # dev | plan
```

| Tipo | Entrega | Oráculo de conclusão |
|---|---|---|
| `dev` | Código | O teste declarado passa |
| `plan` | Um plano | O plano existe e consta em `_planos.md` |

Isso mantém **um único mecanismo**: todo plano gera unidades. Um plano de core, por exemplo, gera
unidades `plan` — cada uma produzindo o plano de um módulo. O oráculo continua verificável por
script, porque a linha aparece na tabela.

Sem isso, planos de nível alto exigiriam uma segunda mecânica de plano; com isso, a diferença fica
contida num campo.

É o `unit_id` que o comentário-cabeçalho cita no código, **não o nome do arquivo**. Isso preserva a
razão original da decisão 21: renomear o slug de uma unidade não quebra referência alguma, porque
nenhuma referência aponta para o filename.

Substitui o esquema de prefixo por módulo (`AU-`, `CA-`) do acervo em `docs/mvp/`, que permanece como
está — sem migração.

### Ciclo quando o teste ainda não existe

O caso comum em trabalho novo, e o que o modelo precisa cobrir explicitamente:

1. A unidade declara `test:` com o caminho do teste **alvo**, mesmo antes de ele existir
2. `state: spec` enquanto o teste não existir ou não passar
3. O modo `implement` escreve **teste e código** — o teste é entregável da unidade, não pré-requisito
4. O gate de saída só promove a `verified` quando o arquivo existe **e** a execução passa

O gate de entrada exige o teste **declarado**, não o teste **existente**. A distinção é o que permite
começar uma unidade nova sem quebrar o ciclo.

---

## Formato do plano

### Alvo — declarado no frontmatter

O plano declara onde suas unidades vão viver, com os mesmos campos da unidade:

```yaml
core: hub
module: mcp
block: ""        # vazio quando o plano não cria bloco
```

O modo `derive` lê esses campos para criar a estrutura e mover o arquivo do `_inbox`. Declarar no
documento, e não na invocação, mantém a decisão registrada onde ela pertence.

**Um plano, um alvo.** Trabalho que cruza módulos é dividido em planos distintos — o modo `review`
sinaliza e recomenda a divisão. Não é restrição arbitrária: deriva do princípio de lote pequeno e
resolve a ambiguidade de para onde mover o arquivo na aprovação.

> O alvo define onde o plano e suas unidades **vivem**, não a fronteira do que o código **toca**. Uma
> unidade pode tocar arquivos de qualquer lugar — é o campo *Arquivos* que declara isso.

### Backlog — região delimitada por marcadores

O script projeta o backlog entre marcadores de comentário, invisíveis no markdown renderizado:

```markdown
<!-- backlog:start -->
| Unidade | Título | Estado |
|---|---|---|
| [0001-01](01-handler-auth.md) | Handler MCP com autenticação obrigatória | `verified` |
| [0001-02](02-search-catalog.md) | Tool search_catalog | `spec` |

1 de 9 verificadas · atualizado em 2026-07-19
<!-- backlog:end -->
```

O script substitui **exatamente** o conteúdo entre os marcadores; o resto do plano é intocável. É o
mesmo princípio do frontmatter na unidade — região delimitada, sem prosa —, aplicado ao corpo.
Parsear headings seria frágil: qualquer texto adicionado na seção se perderia na próxima projeção.

**Por que o backlog não é o índice eliminado.** O índice agregava por core, informação que a
estrutura de pastas já dá. O backlog agrega **por plano** — recorte temporal que a estrutura não
expressa, já que unidades de vários planos convivem na mesma pasta do módulo.

### Bloco obrigatório — Independência

Todo plano declara, no corpo, por que é **um** plano e não dois. Uma seção `## Independência` responde
ao teste: entregando apenas este plano e parando, o sistema fica em estado válido — e não há parte
separável que entregue valor sozinha.

A declaração é feita **no momento da escrita**, não descoberta na revisão: é quando ainda é barato
mudar de ideia. A revisão apenas audita se ela se sustenta (ver *Avaliação de escopo*).

---

## Avaliação de escopo — quando dividir um plano

O check mais importante do modo `review`, e o único com evidência concreta de necessidade dentro do
próprio repositório.

### O caso que originou a regra

O esforço de separar o plugin `amflow` em Worker e Builder foi executado junto com a troca do
mecanismo de conexão com o Hub para MCP. Resultado: funcionalidades com erros e conflitos, e
documentação que não se sustentou.

A evidência está registrada em `docs/mvp/80_fix/`:

| Sinal | Onde |
|---|---|
| O plano do MCP se declara subordinado a outro | `conexao-plugins-hub-mcp.md` — *"dentro da refatoração de separação dos plugins"* |
| E altera decisões de um plano em andamento | mesma fonte — seção *"Impacto nas decisões do split"* |
| Volume total do esforço | **1.826 linhas em cinco documentos** — `escopo` 201 · `separacao` 379 · `conexao` 350 · `conexao-impl` 219 · `runbook` 677 |

Não foi um plano grande demais: foram **dois planos acoplados**, um alterando decisões do outro
enquanto ambos corriam.

### O teste — independência

> Entregando **apenas a parte A** e parando aqui, o sistema fica em estado válido e útil?
> Se a resposta for sim para A **e** para B, são dois planos.

Aplicado ao caso: o split entrega valor sozinho — dois plugins funcionando com REST. A troca para MCP
entrega valor sozinha — conexão MCP no plugin monolítico. Ambos passam isolados; eram dois planos.

### A checagem — concorrência

Determinística, via `_planos.md`: **existe plano `em desenvolvimento` no mesmo core ou módulo?**

Se existe, ou o novo plano espera, ou se declara dependente — e dependência declarada entre planos em
andamento é exatamente o padrão que falhou. Esta checagem sozinha teria sinalizado o caso.

### Quando **não** dividir

Dividir tem custo. Se A depende de B, separá-los cria dependência **entre planos** — o problema
original invertido, e pior, porque a coordenação passa a ser entre documentos numerados independentes.

| Situação | Divisão correta |
|---|---|
| As partes passam no teste de independência | **Planos separados** |
| Dependência sequencial, objetivo único | **Fases** no mesmo plano |
| Agrupamento de capability sob o mesmo módulo | **Blocos** |
| Alvo é domínio novo, não variação | **Módulo novo** |

### O que a avaliação não faz

- **Não impõe teto de unidades.** Tamanho é reportado como contexto — unidades previstas, módulos e
  cores tocados — nunca como critério de reprovação. Um número sem base empírica competiria com o
  teste de independência e dividiria planos coesos.
- **Não bloqueia a aprovação.** Quem aprova é o humano; um check que recusa vira obstáculo a
  contornar. Quando a avaliação sinaliza divisão e a decisão é não dividir, **o plano registra o
  porquê** — mesmo princípio das lacunas `L-XX`. O custo de justificar por escrito já filtra o
  "aproveitando o escopo", que foi exatamente como o caso real começou.
- **Não depende de detectar frases.** Expressões como *"dentro de"*, ou seções de impacto em outro
  plano, são evidência histórica útil — mas morrem como detector: quem conhece a regra deixa de
  escrevê-las, e o acoplamento segue invisível.

---

## Nomenclatura

Mesmo desenho da regra de skills do `build-resource` (linha 80): **sugestão semântica** pela skill,
**validação sintática** pelo script.

### Plano

No `_inbox`, apenas o nome semântico:

```
<intenção>-<alvo>[-<qualificador>]
```

| Parte | O que é | Exemplos |
|---|---|---|
| **Intenção** | substantivo de ação ou tema | `evolve`, `simplify`, `split`, `required-login` |
| **Alvo** | o que é afetado — **sem repetir o caminho** | `dev-units-model`, `new-project-command` |
| **Qualificador** | opcional: fase, camada, variante | `l3`, `impl` |

Restrições: kebab-case, **inglês**, 2–5 tokens, ≤ 64 caracteres, sem conectivos.

> **Por que inglês, se a documentação é pt-BR.** O nome do plano vira o `module` do frontmatter e o
> nome da pasta no disco — e o `.claude/CLAUDE.md` § *Idioma e Nomenclatura* classifica módulo como
> **identificador**, exigindo inglês. As duas normas se contradiziam até 2026-07-28 (ver decisão 32).
> A prosa do plano continua inteiramente em pt-BR: o inglês vale para o **nome**, não para o conteúdo.

**Na aprovação, recebe o número** — 4 dígitos, sequencial global, atribuído uma única vez:

```
_inbox/evolve-tools.md   →   hub/0004-evolve-tools/0004-evolve-tools.md
```

A pasta criada tem **exatamente o mesmo nome** do arquivo. Quando o plano cria um módulo, seu nome
costuma ser o próprio módulo: `_inbox/mcp.md` → `hub/0001-mcp/0001-mcp.md`.

> **"Sem repetir o caminho"** é regra nova, e só faz sentido agora: em `80_fix/` tudo era plano, então
> o nome precisava carregar o contexto inteiro. Em `docs/plan/<core>/<module>/`, o contexto está no
> caminho — um plano em `hub/mcp/` não se chama `evolve-tools-hub-mcp`, e sim `evolve-tools`.

**O plano mantém o nome ao sair do `_inbox`** — nunca vira `plano.md`. Um módulo recebe vários planos
ao longo do tempo, e nome fixo colidiria. Além disso, descartar o nome na aprovação tornaria a regra
inútil justamente onde o documento se torna permanente.

### Unidade

Arquivo: `[nn]-[nome].md` — dois dígitos sequenciais **dentro do plano**, mais o slug semântico.

```
01-handler-auth.md
02-search-catalog.md
```

Três identificadores, com papéis distintos:

| | Forma | Onde aparece | Muda? |
|---|---|---|---|
| **`unit_id`** | `0001-02` | frontmatter, comentário-cabeçalho no código, testes, backlog | **Nunca** |
| **Arquivo** | `02-search-catalog.md` | disco | Ao renomear o slug |
| **Slug** | `search-catalog` | `name:` e no nome do arquivo | Pode |

A separação resolve a tensão entre legibilidade e estabilidade: o arquivo é autoexplicativo ao listar
a pasta, e o `unit_id` — que é o que o código cita — não depende dele. Renomear o slug não quebra
referência alguma.

Slug: mesmas restrições sintáticas do plano, sem repetir o módulo (já está no caminho).

### Tabela de planos

`docs/plan/_planos.md` — registro dos planos **aprovados**, e fonte da numeração:

````markdown
<!-- planos:start -->
| # | Plano | Core | Módulo | Situação | Aprovado |
|---|---|---|---|---|---|
| 0001 | [mcp](hub/0001-mcp/0001-mcp.md) | hub | mcp | em desenvolvimento | 2026-07-20 |
<!-- planos:end -->
````

- **Só entra plano aprovado.** O que está no `_inbox` não aparece — a tabela registra o que entrou em
  desenvolvimento.
- **O número é atribuído aqui:** o script lê o maior em uso e toma o próximo.
- **A situação é projetada, não digitada** — derivada do estado das unidades: `em desenvolvimento`
  enquanto houver unidade fora de `verified`, `concluído` quando todas estiverem.
- Vive em `docs/plan/`, não em `.claude/skills/dev-units/`: é dado do projeto, versionado junto dos
  planos, e sobrevive a qualquer troca da skill.

### Divisão de responsabilidade

| Camada | Onde | O quê |
|---|---|---|
| Sugestão | **Skill** | 3 opções a partir de `core` + `module` + intenção declarada; aceita "outro" |
| Validação sintática | **Script** | Minúsculas e hífens, sem hífen inicial/final/consecutivo, ≤ 64, sem conectivo, sem prefixo numérico |
| Colisão | **Script** | Nome já existente no alvo; próximo ID livre no módulo |

A checagem de colisão não existe na regra de skills e é necessária aqui: o ID sequencial precisa
saber qual é o próximo livre no módulo.

---

## Camada de execução

Operado por **uma skill única**, que delega todo determinismo a scripts.

### Skill `dev-units` — substitui `plan-dev-units`

O plano é insumo, não produto da skill: você o escreve com Opus, a skill revisa e deriva.

| Modo | O que faz |
|---|---|
| `review <plano>` | Os seis checks abaixo |
| `derive <plano>` | Cria a estrutura, move o plano do `_inbox`, gera as unidades, projeta o backlog |
| `implement <unidade>` | Executa em cold-start |

Adicionar um bloco **não é modo próprio** — é um plano cujo alvo é módulo existente, e passa pelo
mesmo `review` → `derive`.

### Modo `review` — os seis checks

Nem todos têm a mesma natureza; separar evita pedir julgamento onde cabe script:

| Check | Natureza | Como |
|---|---|---|
| **O plano precisa ser dividido?** | **Misto** | Script checa concorrência em `_planos.md` e reporta tamanho; julgamento audita a declaração de independência (ver *Avaliação de escopo*) |
| Usou a documentação oficial adequada ao escopo? | **Misto** | Script confere se as fontes citadas existem; julgamento avalia se são as certas |
| Há erros de arquitetura? | Julgamento | O guardrail de dependência que ancorava este check em script foi aposentado — a 0003-08 extraiu `plugins/` para outro repositório, e ele perdeu o par que verificava |
| Há erros conceituais? | Julgamento | — |
| Há lacunas em aberto? | Julgamento | Registrar como `L-XX` |
| É compatível com os padrões do AmFlow? | **Misto** | Guardrails do `CLAUDE.md` são verificáveis; o resto é julgamento |

Quatro dos seis têm parte automatizável. Sem extraí-la, a revisão vira leitura subjetiva — e leitura
subjetiva é onde a variância volta.

### Os dois gates

São a razão de existir da skill:

- **Entrada (`implement`):** unidade sem critério de aceite, sem teste declarado ou sem os campos de
  cold-start → recusa e devolve ao `derive`. Impede começar sem oráculo.
- **Saída:** teste não passa → a unidade não transiciona para `verified`. Impede a doc de mentir.

### Fronteira skill / script

| Responsabilidade | Onde vive |
|---|---|
| Detectar modo, validar gates, medir lote, rodar teste, projetar estado, **validar nome e colisão** | **Script** — Python, em `.claude/skills/dev-units/scripts/` |
| Pesquisar, sintetizar, revisar com julgamento, decidir a fatia, escrever código, **sugerir nomes** | **Skill** |

Os scripts seguem a [norma de linguagem](language-policy.md): Python 3.10 (versão do Cowork), stdlib
pura, verificados com `unittest` via `scripts/test-python.sh`.

Skill interpretando "verifique se está pronto" devolve a variância ao sistema. O que estabiliza é o
oráculo determinístico, e oráculo é código — conforme *Código vs. Instruções em Markdown* no
`CLAUDE.md`.

### Modelos

**Sonnet é o padrão no `implement`**, com override do usuário conforme o escopo do trabalho. O
`review` e o `derive` pedem julgamento denso — Opus.

**A troca não é declarável na skill.** Verificado em 2026-07-19: das skills do projeto que declaram
`model:` no frontmatter (`backlog`, `backlog-worker`, `workflow-runner`), **todas o deixam vazio**;
apenas os agents o usam preenchido (`model: opus`). A skill roda no contexto de quem a invoca e
herda o modelo da sessão.

Consequência: a política é **operacional** — o modelo é escolhido antes de invocar. Se a troca
automática por modo for requisito, e não conveniência, isso reabre a decisão sobre agents.

**Fora do escopo desta fase:** qualquer agent. Agent só se justifica onde há julgamento somado a
pesquisa ampla, e só depois de a skill existir.

---

## Fluxo completo

| # | Etapa | Executor | Resultado |
|---|---|---|---|
| 1 | Plano nasce | Opus | `docs/plan/_inbox/nome.md` |
| 2 | Revisão | skill + script | Cinco checks |
| 3 | **Aprovação** | **humano** | gate |
| 4 | Número atribuído | script | Próximo livre em `_planos.md` — 4 dígitos |
| 5 | Estrutura criada | script | `docs/plan/<core>/<NNNN>-<nome>/` |
| 5b | Plano movido e prefixado | script | `_inbox/<nome>.md` → `<NNNN>-<nome>/<NNNN>-<nome>.md` |
| 6 | Unidades derivadas | Opus | Um arquivo por unidade, densas para cold-start |
| 7 | Backlog projetado | script | No arquivo do plano |
| 8 | Implementação | Sonnet (default) | Uma unidade por vez, em cold-start |
| 9 | Fechamento | script | Estado projetado na unidade e no backlog |

---

## Rastreamento de objetivos

| Origem | Objetivo | Componente |
|---|---|---|
| Inicial | Módulo como organizador; pasta por módulo | 1 |
| Inicial | Adição como bloco aditivo | 1 |
| Inicial | Doc deixa de ser PRD e vira o módulo | 2 |
| Inicial | Índice do sistema com link para o módulo | 1 — a hierarquia de pastas é auto-descritiva |
| Novo | Nível core para evoluir sob Clean Architecture | 1, 3 |
| Novo | Modular com blocos (Google/email como bloco) | 1 |
| Novo | Documentação é código em produção | 2 |
| Novo | Código documentado com inteligência | 5 |
| Novo | Índice para orientar agente e desenvolvedor | 1 — idem |
| Novo | Princípios, guidelines, guardrails, referências | 3 |
| Novo | Revisão de plano sugerindo blocos | 4, modo `review` |
| Novo | Quebrar plano em fases e fases em unidades | 4 |
| Novo | **Cold-start com Sonnet sem pedido manual** | Conceitos, modo `derive` |
| Novo | **Backlog do plano com as unidades** | 2 — projeção |
| Novo | **Registro de conclusão na unidade e no plano** | 2 — duas projeções, uma fonte |
| Auditoria | 0/18 com critério de aceite | 2 |
| Auditoria | 0/18 ligados a teste | 2 |
| Auditoria | 18/18 `draft`; sem estado | 2 |
| Auditoria | Lote sem norma | 4 |
| Auditoria | 90 refs código↔doc; lacunas; racional | 5 |

---

## Decisões

### Resolvidas em 2026-07-19

| # | Decisão | Resolução |
|---|---|---|
| 1 | Norma de lote | **8 passos** (p90 das 86 unidades); sem sequência = incompleta |
| 2 | Grão de bloco e unidade | Bloco é **pasta**; unidade é **arquivo** (exigência do cold-start) |
| 3 | Como o estado é computado | **Declaração na spec** (`spec → teste`), granularidade de arquivo |
| 4 | Onde vive a normativa de domínio | **`<core>/system/`**; transversal em `security/system/` |
| 5 | Cobertura da normativa | Cada core ganha a sua, conforme for tocado |
| 6 | Localização dos docs | **`docs/plan/`** para o novo; `docs/mvp/` somente leitura |
| 7 | Migração do acervo | **Não migrar agora** — tarefa futura |
| 8 | Modelo de desenvolvimento | **Sonnet** por padrão, com override do usuário |
| 9 | Security | **Core transversal**, dono do módulo de autenticação, hospedado no Hub |
| 10 | Índice | **Eliminado** — substituído pela estrutura + backlog + consulta sob demanda |
| 11 | Vocabulário | Inglês em código, caminhos e frontmatter; **português na prosa** |
| 12 | Formato da unidade | Definido; referência viva em `docs/plan/hub/0001-mcp/01-handler-auth.md` |
| 13 | Regiões de escrita | Script escreve só o bloco `# verificação` do frontmatter; nunca o corpo |
| 14 | Identificador da unidade | `unit_id` = `[nº plano]-[nº unidade]`, ex. `0001-02` — **revisa** o prefixo por módulo (`MC-`, `AU-`) |
| 15 | Teste inexistente | Gate de entrada exige teste **declarado**, não existente; `implement` escreve teste e código |
| 16 | Alvo do plano | Frontmatter com `core`/`module`/`block`; **um plano, um alvo** |
| 17 | Backlog | Marcadores `<!-- backlog:start -->` / `<!-- backlog:end -->`; script substitui só o miolo |
| 18 | Modelo por modo | **Não declarável em skill** — política operacional; automatizar exigiria agent |
| 19 | Nome do plano | Mantém o nome ao sair do `_inbox` e **recebe prefixo numérico**; nunca vira `plano.md` |
| 20 | Regra de nome | `<intenção>-<alvo>[-<qualificador>]`, kebab-case, sem repetir o caminho — idioma **revisado** pela decisão 32 |
| 21 | Arquivo da unidade | `[nn]-[nome].md` — **revisa** "só o ID"; a estabilidade vem do `unit_id`, não do filename |
| 22 | Numeração do plano | **4 dígitos**, sequencial global, atribuída na aprovação; **pasta = nome do arquivo** |
| 23 | Numeração da unidade | **2 dígitos, por plano** — recomeça em `01` a cada plano novo |
| 24 | Tabela de planos | `docs/plan/_planos.md` — só aprovados; fonte da numeração; situação projetada |
| 25 | Avaliação de escopo | Teste de **independência** declarado na escrita do plano, auditado na revisão; concorrência checada em `_planos.md` |
| 26 | Divisão não bloqueia | Sinaliza e exige registro do porquê quando não se divide; **sem teto de unidades** |
| 27 | Alvo do plano | Sempre `core`/`module`/`block` — não existe alvo `system` |
| 28 | Tipo de unidade | `unit_type: dev \| plan`; a unidade `plan` produz um plano, com oráculo em `_planos.md` |
| 29 | Relação entre planos | Coluna **Origem** em `_planos.md` — qual unidade de qual plano o gerou |
| 30 | Natureza deste documento | **Norma**, não plano; a implementação é o plano `0002-dev-units` |

### Resolvida em 2026-07-24

| # | Decisão | Resolução |
|---|---|---|
| 31 | Linguagem e verificação dos scripts | **Python 3.10** (versão do Cowork), stdlib pura, `unittest` via `scripts/test-python.sh` — ver [`language-policy.md`](language-policy.md) |

> A pendência de infra de teste que travava este modelo não era técnica: vinha do bloqueio "sem
> Python", revogado pela [norma de linguagem](language-policy.md) com base em medição. O oráculo
> determinístico previsto no componente 5 deixa de depender de uma decisão em aberto.

### Resolvida em 2026-07-28

| # | Decisão | Resolução |
|---|---|---|
| 32 | Idioma do nome de plano, módulo e unidade | **Inglês** — **revisa** a decisão 20, que dizia pt-BR |

> **O conflito que a originou.** A decisão 20 exigia pt-BR no nome; o `.claude/CLAUDE.md` § *Idioma e
> Nomenclatura* exige inglês em identificadores e nomeia **módulo** entre eles. Como o nome do plano
> vira o `module` do frontmatter e a pasta no disco, as duas normas se contradiziam — e o conflito só
> apareceu quando o terceiro plano precisou de um nome que não fosse termo técnico.
>
> **Custo de migração: zero.** Os planos `0001-mcp` e `0002-dev-units` já eram termos técnicos em
> inglês; nenhum renomeio. O primeiro plano escrito sob esta decisão é `0003-public-catalog`.
>
> **O que não muda:** a prosa. Documentação, plano e unidade seguem inteiramente em pt-BR — o inglês
> vale para o identificador, nunca para o conteúdo.

### Pendentes

1. **Alinhamento do `CLAUDE.md`.** A regra de precedência foi **antecipada em 2026-07-19**. Restam as
   doze referências a `docs/mvp` e a desambiguação entre o **Core Engine** (visão futura, telemetria)
   e a pasta **`system/`** — ambas acompanham a migração.
2. **Troca automática de modelo por modo.** Só é possível com agent (ver *Modelos*). Se for
   requisito, e não conveniência, reabre a decisão sobre agents — hoje fora de escopo.
> **Resolvidas nesta rodada:** as regiões no `index.md`, pelo mecanismo de marcadores (ver *Formato
> do plano*) — o mesmo padrão serve a qualquer arquivo com conteúdo humano e projeção de script no
> mesmo corpo; e a migração da unidade-referência, executada em 2026-07-20 junto com a criação do
> plano `0001` e da tabela `_planos.md`.

---

## Referências

**Evidência empírica**
- METR (2025), *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer
  Productivity* — https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- DORA (2024), *Accelerate State of DevOps Report* — https://dora.dev/research/2024/dora-report/
- DORA (2025), *State of AI-assisted Software Development* — https://dora.dev/dora-report-2025/

**Análise de métodos**
- Böckeler, B., *Understanding Spec-Driven Development: Kiro, spec-kit e Tessl* —
  https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- GitHub Spec Kit — https://github.com/github/spec-kit

**Interno**
- Norma de linguagem dos scripts: [`language-policy.md`](language-policy.md)
- Evidência que a fundamenta: [`estudo-runtime-e-dependencias.md`](estudo-runtime-e-dependencias.md)
- Padrão atual: `.claude/skills/dev-units/SKILL.md`
- Exemplo mais maduro: [`hub/back/auth/dev-units.md`](../../mvp/20_delivery/hub/back/auth/dev-units.md)
- Restrições de processo e frontmatter: `.claude/CLAUDE.md`

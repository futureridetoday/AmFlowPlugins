---
# about
name: help
type: command
project: AmFlow
description: Explica um recurso que você adquiriu no AmFlow — lista as licenças ativas e exibe a descrição do recurso escolhido
tags: [help, ajuda, worker, documentacao, recursos]

# history
author: Bortoli
created: 2026-08-20
status: draft
version: 1.0.0
updated: ""

# system
scope: global
auto_load: false
dependencies: []

# hub
hub_id: ""
source: ""
price: 0
---

# /amflow-worker:help

Lista os recursos que o usuário adquiriu no AmFlow e explica o que ele escolher, a partir do
`[tipo]-description.md` instalado junto com o recurso.

Aceita também o nome direto: `/amflow-worker:help deep-research` pula a lista e vai à descrição.

## Fase 0 — Autenticação (obrigatória)

Antes de qualquer outra ação, chame a tool `list_active_licenses` do servidor MCP `amflow-worker`.

- Sucesso → siga com a lista devolvida.
- Sem sessão / erro → o conector `amflow-worker` não está autorizado nesta sessão. **Encerre aqui.** Oriente o
  usuário a autorizar o conector via `/mcp` e reexecutar.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente.

## Processo

### 1. Listar

A tool devolve `name`, `type`, `version` e `visibility` de cada recurso licenciado — inclusive os
herdados de organizações.

Lista vazia → informe **"Você ainda não tem nenhum recurso do AmFlow. Explore o catálogo em
amflow.work"** e encerre.

Para cada item, verifique se está instalado, procurando o arquivo principal em `~/.claude/` e no
projeto atual:

| Tipo | Caminho |
|---|---|
| `skill` | `skills/<name>/SKILL.md` |
| `agent` | `agents/<name>/<name>.md`, ou `agents/<name>.md` em instalação anterior ao layout de diretório |
| `command` | `commands/<name>.md` |
| `hook` | `hooks/<name>/hook.json` |

Exiba uma lista numerada, marcando o que não está instalado:

```
Seus recursos do AmFlow:

1. deep-research (skill · v1.2.0)
2. code-reviewer (agent · v2.0.0)
3. primal-branding (skill · v1.0.0) — não instalado

Qual deles você quer entender? Responda o número ou o nome.
```

Com o nome vindo no argumento, pule para o passo 2 direto.

### 2. Resolver a escolha

Número → o item daquela posição. Nome → casamento exato pelo `name`; havendo mais de um tipo com o
mesmo nome, pergunte qual.

Escolha fora da lista → informe que o recurso não está entre as licenças ativas e reexiba a lista.

### 3. Exibir a descrição

Leia o `[tipo]-description.md` na raiz da pasta do recurso — `skill-description.md`,
`agent-description.md` —, procurando primeiro no projeto atual e depois em `~/.claude/`.

Apresente em prosa, no chat: comece pelo *O que é* e pelo *Como usar*, que é o que responde a pergunta
mais comum, e ofereça o restante — problema que resolve, como funciona, exemplos, fundamentação, base
de conhecimento e limites.

Se o usuário já disse o que quer saber ("quais os limites do X?"), vá direto à seção correspondente.

**Nunca invente conteúdo de seção.** Seção ausente é reportada como ausente.

### 4. Casos sem descrição

| Situação | Resposta |
|---|---|
| Recurso **não instalado** | `<nome> está na sua conta mas não está instalado neste projeto. Instale com /amflow-worker:install <nome> e eu explico.` |
| Instalado, **sem** o documento | Recurso publicado antes do padrão de descrição. Resuma a partir do `description` do frontmatter, avisando que é a descrição curta e que o recurso não traz documentação completa |
| Tipo `command` ou `hook` | Ainda fora da norma de descrição. Mesma resposta do caso acima |

## Restrições

- **Não instala nada.** Este comando explica; instalar é `/amflow-worker:install`.
- **Não consulta o catálogo.** A fonte é o disco. Recurso licenciado e não instalado não é explicado
  aqui — a descrição dele está na página do recurso no Hub.
- **Não inventa conteúdo.** O que o documento não diz, o comando não responde.

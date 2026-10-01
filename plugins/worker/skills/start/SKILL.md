---
name: start
description: Abre a sessão no projeto atual — confere o login no AmFlow, relê o CLAUDE.md do projeto e devolve a identidade dele em duas linhas.
license: Proprietary
disable-model-invocation: true
allowed-tools: mcp__plugin_amflow-worker_amflow-worker__iam
metadata:
  amflow-version: "1.0.0"
  amflow-status: in_progress
  amflow-author: Bortoli
  amflow-author-id: 985920db-502d-4cb3-9ca1-c145719a9307
  amflow-updated: "2026-10-01"
  amflow-tags: start onboarding session context worker
  amflow-dependencies: ""
---

# /amflow-worker:start

Abre a sessão no projeto atual: confere o login, relê as instruções do projeto e devolve a
identidade dele.

**Por que reler o `CLAUDE.md` se ele já carregou.** Numa sessão que já andou, o arquivo fica longe
do ponto onde o trabalho acontece. A releitura recoloca as instruções perto da tarefa; o custo de o
arquivo entrar duas vezes no contexto é aceito de propósito.

## Autenticação

<!-- auth-check:start — cópia de auth/auth-check.md; editar lá, nunca aqui -->
Antes de qualquer outra ação do comando, chame a tool `iam` do servidor MCP `amflow-worker`, sem
argumentos.

| Resultado | O que fazer |
|---|---|
| Responde com `user_id` | Sessão válida. Siga com o comando, sem comentar a verificação |
| Tool indisponível na sessão, ou `Autenticação necessária.` | **Encerre aqui.** Diga que o conector `amflow-worker` não está autorizado nesta sessão e oriente o usuário a autorizá-lo pelo `/mcp` e repetir o comando |
| Outro erro | **Encerre aqui.** Mostre o erro como veio, sem mandar autorizar o conector de novo |

Sem login, o conector não conecta e a tool `iam` nem aparece na sessão — esse é o caso da segunda
linha, não um erro do Hub.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.
<!-- auth-check:end -->

## Instruções

Tudo é leitura — nada aqui altera estado, nada pede confirmação.

1. Ler `.claude/CLAUDE.md` com a ferramenta Read.
2. Se houver `CLAUDE.md` na raiz do projeto além do de `.claude/`, ler os dois — ambos carregam, e o
   conflito entre eles é a primeira coisa a reportar.
3. Sem `.claude/CLAUDE.md`, dizer que o projeto não está configurado e encerrar. Não sugerir
   comando.

## Output

Duas linhas, escritas a partir do título e da visão geral do `CLAUDE.md` — nunca de campo de
frontmatter, que o arquivo pode não ter:

```
<nome do projeto> — <o que ele é, numa linha>
<uma frase: o que ele faz, para quem, ou o que o distingue>
```

Terminar aqui. Não propor trabalho, não perguntar o que o usuário quer fazer.

## Invariantes

- Somente leitura. Nunca escrever, nunca alterar estado.
- Nunca despejar o conteúdo do `CLAUDE.md` na tela — ele já está no contexto.
- Ausência de arquivo nunca é erro — é informação. Reportar e seguir.

Antes de qualquer outra ação do comando, chame a tool `iam` do servidor MCP `amflow-worker`, sem
argumentos. Chame-a sozinha e espere a resposta: nenhuma outra chamada de tool antes do resultado,
nem em paralelo com ela.

| Resultado | O que fazer |
|---|---|
| Responde com `user_id` | Sessão válida. Siga com o comando, sem comentar a verificação |
| Tool indisponível na sessão, ou `Autenticação necessária.` | **Encerre aqui.** Diga que o conector `amflow-worker` não está autorizado nesta sessão e oriente o usuário a autorizá-lo pelo `/mcp` e repetir o comando |
| Outro erro | **Encerre aqui.** Mostre o erro como veio, sem mandar autorizar o conector de novo |

Sem login, o conector não conecta e a tool `iam` nem aparece na sessão — esse é o caso da segunda
linha, não um erro do Hub.

Nunca exiba tokens — a sessão OAuth é gerida pelo cliente, fora do contexto do modelo.

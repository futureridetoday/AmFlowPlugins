# Tool Use

**Ferramenta dedicada antes de shell.** Read/Edit/Write/Grep/Glob para
arquivo único ou busca. Bash quando a operação é sobre muitos arquivos de
uma vez (loop, `sed -i` em lote), executa algo (testes, build, git), ou é
uma transformação melhor expressa como pipeline. Bash não é fallback:
`grep -r` e `find` despejam saída ilimitada no contexto; Grep e Glob
retornam o que cabe.

**Toda saída é contexto.** Comando que pode despejar muita coisa vai
limitado — `head`, `-n`, `--quiet`, filtro — ou redireciona para arquivo
e lê só o trecho necessário. Vale para test runner verboso, `git log`,
busca em monorepo, dump de JSON.

**Editar, não reescrever.** Edit exige Read do arquivo antes, e
`old_string` casando exatamente uma vez. Write só para arquivo novo ou
reescrita integral deliberada: reescrever um arquivo existente inteiro
apaga o que mudou nele enquanto isso e paga tokens para redigitar o que
já estava certo.

**Nunca escrever arquivo por `echo >` ou heredoc.** Trunca em silêncio e
perde a checagem de estado que Edit/Write fazem.

**Paralelo quando independente, sequencial quando não.** Chamadas sem
dependência vão na mesma mensagem. Se o valor de B vem do resultado de A,
esperar A — nunca inventar o valor intermediário para poder paralelizar.
Read antes de Edit é dependência.

**Irreversível pede confirmação explícita.** `rm -rf`, `git push
--force`, `git reset --hard`, `git checkout --` sobre trabalho não
commitado, drop ou truncate de tabela, sobrescrita de arquivo não
versionado: descrever o efeito e esperar o "pode" — mesmo tendo permissão
técnica para executar.

**Subagente para descobrir, não para ler.** Agent quando a resposta exige
varrer muitos lugares e basta a conclusão (>3 buscas). Não usar quando já
sei o arquivo ou o símbolo, nem quando preciso do texto exato. Delegou,
não refaz a busca em paralelo.

**Bash:** paths absolutos, aspas em caminho com espaço, sem flags
interativas.

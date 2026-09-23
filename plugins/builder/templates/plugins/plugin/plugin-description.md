<!-- Destino: plugins/<nome>/plugin-description.md — raiz da pasta do plugin, ao lado de
     .claude-plugin/plugin.json.

     Plugin é diretório: plugins/<nome>/.claude-plugin/plugin.json + plugin-description.md,
     mais os componentes que o plugin usar (commands/, agents/, skills/, hooks/, .mcp.json...)
     soltos na raiz da pasta — nunca dentro de .claude-plugin/.

     Markdown puro: sem frontmatter, sem YAML, sem JSON. Os metadados já vivem no plugin.json.

     O leitor é quem NÃO conhece o plugin — alguém decidindo se instala, um Creator avaliando
     se usa como dependência. O GUIDE.md e o plugin.json dizem como o plugin é construído e
     configurado; este arquivo diz o que ele é e quando vale instalar.

     Títulos exatos e nesta ordem. Fundamentação e Base de conhecimento são opcionais; as
     outras seis não. Subtítulos ### são livres por dentro. -->

# plugin-name

<!-- O valor exato do campo `name` do plugin.json. É identificador, não título editorial. -->

Versão 1.0.0

<!-- Linha isolada, na forma `Versão X.Y.Z`. Precisa bater com o `version` do plugin.json —
     ao subir a versão do plugin, subir aqui também. -->

## O que é

<!-- Uma frase, para quem não conhece o domínio. O que o plugin entrega, dito como se descreve
     uma ferramenta a alguém que vai decidir instalá-la. -->

## Problema que resolve

<!-- Por que isto existe como plugin — o que falta no Claude Code sem ele, e por que a resposta
     é um plugin (comandos, agents, skills, hooks ou MCP juntos) em vez de um recurso solto. -->

## Como funciona

<!-- Os componentes que o plugin bundla — quais commands, agents, skills, hooks ou servidores
     MCP ele registra — e o que cada um cobre. Se depende de configuração do usuário
     (userConfig) ou de outro plugin (dependencies), diga aqui. -->

## Como usar

<!-- Como instalar (marketplace, caminho local, skills-dir) e o primeiro passo depois de
     instalado — o comando a rodar, o agent a invocar, ou o gatilho que ativa a skill/hook
     sozinho. -->

## Exemplos de uso

<!-- Dois a quatro cenários concretos. Cada um: a situação, o que foi pedido ao plugin, o que
     ele devolveu. -->

## Fundamentação

<!-- Opcional. Só nomes — o método, a spec ou o padrão em que o plugin se apoia —, numa linha,
     sem explicação. Sem nome a citar, remova a seção inteira: seção forçada produz texto de
     enchimento, que é pior que a ausência. -->

## Base de conhecimento

<!-- Opcional. Só quando o plugin tem references/ ou assets/ com arquivos de dados dentro —
     pasta vazia ou só com .gitkeep não conta. Sem isso, remova a seção inteira — ausência não
     se declara. -->

## Limites

<!-- Lista de até cinco itens, uma frase curta cada (≈ 80 caracteres): o que o plugin não
     oferece espontaneamente e quem resolve o que fica de fora. -->

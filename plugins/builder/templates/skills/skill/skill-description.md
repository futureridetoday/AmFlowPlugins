<!-- Destino: skills/<nome>/skill-description.md — raiz da pasta da skill, ao lado do SKILL.md.

     Markdown puro: sem frontmatter, sem YAML, sem JSON. Os metadados já vivem no SKILL.md.

     O leitor é quem NÃO conhece a skill — um stakeholder avaliando, um comprador decidindo,
     um usuário que acabou de instalar. O SKILL.md diz como executar; este arquivo diz o que é
     e quando cabe. Se uma seção começar a virar procedimento, ela está no arquivo errado.

     Títulos exatos e nesta ordem — o gate compara literal. Fundamentação e Base de conhecimento
     são opcionais; as outras seis não. Subtítulos ### são livres por dentro. -->

# skill-name

<!-- O valor exato do campo `name` do SKILL.md. É identificador, não título editorial. -->

Versão 1.0.0

<!-- Linha isolada, na forma `Versão X.Y.Z`. Precisa bater com o `version` do SKILL.md —
     ao subir a versão da skill, subir aqui também. -->

## O que é

<!-- Uma frase, para quem não conhece o domínio. Se ela só faz sentido para quem já usou a
     skill, está errada. Diga a categoria da coisa antes da particularidade dela. -->

## Problema que resolve

<!-- Por que a skill existe e o que custa não tê-la. Descreva o trabalho como ele é feito sem
     ela, e onde esse jeito falha. É a seção que decide se o leitor continua lendo. -->

## Como funciona

<!-- O processo que a skill executa, em mecanismo — não em passo a passo de execução.
     O que ela lê, o que decide, o que produz, em que ordem e por quê.
     Se a skill tem script, diga o que ele resolve de forma determinística e por que isso
     importa; não documente a interface dele aqui. -->

## Como usar

<!-- O gatilho que a invoca: a frase que o usuário diz, o comando que ele digita, ou o momento
     em que o Claude a carrega sozinho. Depois, o que ele precisa ter em mãos.
     Escreva do ponto de vista de quem pede, não de quem executa. -->

## Exemplos de uso

<!-- Dois a quatro cenários concretos. Cada um: a situação, o que o usuário pediu, o que
     recebeu. Exemplo não é lista de comandos — é uma história curta com resultado. -->

## Fundamentação

<!-- Opcional. Só nomes — o método, a teoria, a norma ou o padrão —, numa linha, sem explicação.
     Sem nome a citar, remova a seção inteira: seção forçada produz texto de enchimento, que é
     pior que a ausência. -->

## Base de conhecimento

<!-- Opcional. Só quando a pasta do recurso tem `references/` ou `assets/` com arquivos de dados dentro —
     pasta vazia ou só com `.gitkeep` não conta. Sem isso, remova a seção inteira — ausência não se
     declara. -->

## Limites

<!-- Lista de até cinco itens, uma frase curta cada (≈ 80 caracteres): o que o autor não oferece
     espontaneamente e quem resolve o que fica de fora. É a informação que mais evita compra
     errada e avaliação ruim. -->

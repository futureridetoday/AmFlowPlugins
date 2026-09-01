# Por que o frontmatter de skill é assim

O `check.py` vendorizado decide se um `SKILL.md` está correto — dezessete regras, cada uma citada
por número quando reprova. Esta referência não repete essas regras; explica por que elas existem,
para o momento em que a dúvida é de julgamento, não de sintaxe.

## Três blocos, três donos

O topo do `SKILL.md` mistura três origens, e cada uma tem uma regra diferente:

| Bloco | Dono | Onde vive |
|---|---|---|
| `name`, `description`, `license`, `compatibility`, `allowed-tools`, `metadata` | Spec Agent Skills | topo |
| `when_to_use`, `effort`, `model`, `context`, e as demais extensões | Claude Code | topo, condicional — só quando carrega comportamento |
| `amflow-version`, `amflow-status`, `amflow-author`, e as demais chaves do AmFlow | AmFlow | dentro de `metadata`, nunca no topo |

Dado do AmFlow nunca sobe para o topo porque o topo é território da spec e do Claude Code — subir
lá criaria um campo que nenhum dos dois reconhece. A spec já reservou `metadata` exatamente para
isso: um lugar para extensão de plataforma.

## Por que o prefixo `amflow-`

Sem prefixo, um campo do AmFlow pode colidir de nome com um campo de outro dono. Já aconteceu: a
API de skills devolve `source: "custom"` — dizendo como a skill chegou à conta — sem relação
nenhuma com `amflow-source` (de onde a skill veio no Hub, `hub/tipo/nome@versão`). Nomes iguais,
donos diferentes. Sem o prefixo não haveria como saber, só de olhar a chave, a quem um valor
pertence.

## Por que `metadata` só aceita string

A spec define `metadata` como mapa de string para string. Valor que não seja string — lista,
número, booleano — não dá erro: **desaparece em silêncio**. É a única regra deste grupo em que
errar não avisa, e é por isso que existe verificador: lendo o arquivo, um humano não distingue "o
campo não foi declarado" de "foi declarado errado e descartado".

## Por que nunca declarar o valor default

`disable-model-invocation: false`, `context: ""`, `shell: bash` — declarar isso não muda
comportamento nenhum, em lugar nenhum. A razão não é técnica: nada quebra, nada é recusado por
causa disso. É higiene de leitura — um campo a mais para manter em dia, sem efeito algum quando
está no valor que já seria o padrão.

## Por que a norma completa não está aqui

A norma inteira vive em `skill-frontmatter.md`, no repositório onde o Builder é desenvolvido — e é
recurso de sistema: não viaja para dentro de skill publicada. Esta referência é a versão que viaja:
explica o porquê, e delega o "está certo?" ao `check.py` que a acompanha neste mesmo plugin.

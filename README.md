# AmFlowPlugins

Catálogo público dos plugins do [AmFlow](https://amflow.work) para o Claude Code.

> Este repositório é a fonte instalável dos plugins — e a documentação autoritativa deles. O
> desenvolvimento do produto AmFlow acontece em outro repositório; aqui vive apenas o que é
> necessário para instalar e usar os plugins.

## Plugins

| Plugin | Papel |
|---|---|
| [`amflow-worker`](plugins/worker) | Instala e executa os recursos que você adquiriu no Hub AmFlow |
| [`amflow-builder`](plugins/builder) | Cria e publica recursos no Hub AmFlow |

## Instalação

No Claude Code:

```
/plugin marketplace add futureridetoday/AmFlowPlugins
/plugin install amflow-worker@amflow
/plugin install amflow-builder@amflow
```

## Estrutura

```
.claude-plugin/marketplace.json   catálogo — declara os dois plugins abaixo
plugins/worker/                   plugin amflow-worker
plugins/builder/                  plugin amflow-builder
```

## Licença

MIT — ver [LICENSE](LICENSE).

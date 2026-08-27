---
name: setup-claude
description: Configura ou atualiza o CLAUDE.md do projeto atual via perguntas guiadas — identidade, stack e campos de contexto para o Claude
license: Proprietary
metadata:
  amflow-version: "1.0.0"
  amflow-status: review
  amflow-author: Bortoli
  amflow-author-id: 985920db-502d-4cb3-9ca1-c145719a9307
  amflow-updated: "2026-08-27"
  amflow-tags: setup claude-md config creator
  amflow-dependencies: ""
---

# Setup Claude

Configura ou atualiza o `CLAUDE.md` do projeto atual via perguntas guiadas. Invocada via `/amflow-builder:setup-claude` ou pelo Claude ao detectar projeto sem `CLAUDE.md`.

## Quando usar

- Projeto sem `.claude/CLAUDE.md`
- Creator quer atualizar os campos de contexto do projeto
- Invocação explícita via `/amflow-builder:setup-claude`

## Não usar quando

- O projeto usa `/amflow-builder:new-project` para onboarding completo (criação de diretórios + CLAUDE.md)
- O `CLAUDE.md` já está correto e atualizado

## Processo

1. Verificar se `.claude/CLAUDE.md` existe no projeto atual (`pwd`):
   - Não existe → informar o usuário e gerar novo arquivo.
   - Existe → ler com Read e exibir os campos atuais para revisão.

2. Coletar informações via perguntas guiadas:

   | Campo | Pergunta |
   |---|---|
   | `name` | Nome do projeto |
   | `description` | Descrição em uma frase |
   | `project_type` | Tipo: Design / Development / Marketing / AI Builder |
   | Stack técnico | Linguagens, frameworks e serviços principais |
   | Restrições | Regras de negócio, convenções e limitações do projeto |

3. Se o arquivo já existia: exibir resumo das mudanças antes de gravar.

4. Obter `author` e `created`:

   ```bash
   AUTHOR=$(git config user.name 2>/dev/null || git config --global user.name 2>/dev/null)
   DATA=$(date +%Y-%m-%d)
   ```

5. Gerar ou sobrescrever `.claude/CLAUDE.md` com a ferramenta Write:
   - Frontmatter completo (`type: instruction`, `auto_load: true`, campos coletados, `author_id: "<user_id>"` quando fornecido pela Fase 0 do comando invocador)
   - `## Identidade` — tabela com tipo
   - `## Visão Geral` — descrição coletada
   - `## Arquitetura` — estrutura de pastas relevante ao tipo (se houver stack definido)
   - `## Recursos Instalados` — vazia (para preenchimento futuro)
   - `## Restrições` — restrições coletadas + padrões Git (`PRs para main exigem revisão manual` / `Nunca fazer force push em main`) + autonomia (`Decisões arquiteturais exigem aprovação prévia` / `Ações que afetam mais de 5 arquivos exigem plano`)

6. Exibir os arquivos criados ou atualizados.

## Restrições

- Nunca sobrescrever `.claude/CLAUDE.md` sem exibir o resumo de mudanças primeiro (quando o arquivo já existe).
- `AUTHOR` vazio → omitir o campo `author` no frontmatter, não bloquear execução.
- O campo `type` do frontmatter deve ser sempre `instruction`.

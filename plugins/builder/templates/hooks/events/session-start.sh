#!/usr/bin/env bash
# Hook: SessionStart
# Executa quando uma sessão do Claude Code é iniciada.
# Recebe JSON via stdin com informações da sessão.
# Usos: carregar contexto, verificar pré-requisitos, exibir status do ambiente.

set -euo pipefail

INPUT=$(cat)

# Extrair campos em uma única chamada ao Python
eval "$(echo "$INPUT" | python3 -c "
import sys, json, shlex
d = json.load(sys.stdin)
session_id = d.get('session_id', '')
project_dir = d.get('cwd', '')
print('SESSION_ID=' + shlex.quote(session_id))
print('PROJECT_DIR=' + shlex.quote(project_dir))
" 2>/dev/null || echo "SESSION_ID='' PROJECT_DIR=''")"

# ── INJETAR CONTEXTO DA SESSÃO ───────────────────────────────────────────────
# Texto escrito no stdout é injetado no contexto inicial do Claude.

# echo "Sessão iniciada em: $PROJECT_DIR"
# echo "Branch: $(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo 'não é um repo git')"

# ── VERIFICAR PRÉ-REQUISITOS ────────────────────────────────────────────────

# REQUIRED_TOOLS=("git" "python3" "node")
# for tool in "${REQUIRED_TOOLS[@]}"; do
#   if ! command -v "$tool" &>/dev/null; then
#     echo "Aviso: $tool não encontrado no PATH." >&2
#   fi
# done

# ── AUDITORIA ───────────────────────────────────────────────────────────────

# LOG_FILE="${HOME}/.claude/logs/sessions.log"
# mkdir -p "$(dirname "$LOG_FILE")"
# echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") START session=$SESSION_ID dir=$PROJECT_DIR" >> "$LOG_FILE"

exit 0

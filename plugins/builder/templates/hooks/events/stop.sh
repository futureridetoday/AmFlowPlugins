#!/usr/bin/env bash
# Hook: Stop
# Executa quando Claude termina um turno (após entregar a resposta).
# Recebe JSON via stdin com informações do turno encerrado.
# Usos: notificação de conclusão, log de turno, ações pós-resposta.

set -euo pipefail

INPUT=$(cat)

eval "$(echo "$INPUT" | python3 -c "
import sys, json, shlex
d = json.load(sys.stdin)
print('SESSION_ID=' + shlex.quote(d.get('session_id', '')))
" 2>/dev/null || echo "SESSION_ID=''")"

# ── NOTIFICAÇÃO DE CONCLUSÃO ────────────────────────────────────────────────
# Útil quando Claude executa tarefas longas em background.

# osascript -e 'display notification "Claude terminou o turno." with title "Claude Code"' 2>/dev/null || true

# ── AUDITORIA ───────────────────────────────────────────────────────────────

# LOG_FILE="${HOME}/.claude/logs/sessions.log"
# mkdir -p "$(dirname "$LOG_FILE")"
# echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") STOP  session=$SESSION_ID" >> "$LOG_FILE"

exit 0

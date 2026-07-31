#!/usr/bin/env bash
# Hook: SubagentStop
# Executa quando um subagente retorna ao agente principal.
# Recebe JSON via stdin com o resultado do subagente.
# Usos: log de delegação, validação de output, auditoria de subagentes.

set -euo pipefail

INPUT=$(cat)

eval "$(echo "$INPUT" | python3 -c "
import sys, json, shlex
d = json.load(sys.stdin)
print('AGENT_NAME=' + shlex.quote(d.get('agent_name', '')))
print('SESSION_ID=' + shlex.quote(d.get('session_id', '')))
print('OUTPUT=' + shlex.quote(d.get('output', '')))
" 2>/dev/null || echo "AGENT_NAME='' SESSION_ID='' OUTPUT=''")"

# ── AUDITORIA ───────────────────────────────────────────────────────────────

# LOG_FILE="${HOME}/.claude/logs/subagents.log"
# mkdir -p "$(dirname "$LOG_FILE")"
# echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") SUBAGENT_STOP agent=$AGENT_NAME session=$SESSION_ID" >> "$LOG_FILE"

# ── VALIDAÇÃO DE OUTPUT ──────────────────────────────────────────────────────
# Texto escrito no stdout é injetado no contexto do agente principal.

# if [[ -z "$OUTPUT" ]]; then
#   echo "Aviso: subagente $AGENT_NAME retornou sem output." >&2
# fi

exit 0

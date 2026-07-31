#!/usr/bin/env bash
# Hook: PostToolUse
# Executa após qualquer chamada de ferramenta.
# Recebe JSON via stdin com ferramenta, input e output da execução.
# Usos: lint, log, notificação, validação de output.

set -euo pipefail

INPUT=$(cat)

# Extrair campos em uma única chamada ao Python
eval "$(echo "$INPUT" | python3 -c "
import sys, json, shlex
d = json.load(sys.stdin)
tool = d.get('tool', '')
command = d.get('input', {}).get('command', '').replace('\n', ' ')
file_path = d.get('input', {}).get('file_path', '')
exit_code = str(d.get('output', {}).get('exit_code', ''))
print('TOOL=' + shlex.quote(tool))
print('COMMAND=' + shlex.quote(command))
print('FILE_PATH=' + shlex.quote(file_path))
print('EXIT_CODE=' + shlex.quote(exit_code))
" 2>/dev/null || echo "TOOL='' COMMAND='' FILE_PATH='' EXIT_CODE=''")"

# ── LINT PÓS-EXECUÇÃO ───────────────────────────────────────────────────────
# Rodar lint após edição de arquivos.

# if [[ "$TOOL" == "Edit" || "$TOOL" == "Write" ]] && [[ "$FILE_PATH" == *.py ]]; then
#   ruff check "$FILE_PATH" || true
# fi

# ── AUDITORIA ───────────────────────────────────────────────────────────────

# LOG_FILE="${HOME}/.claude/logs/tool-use.log"
# mkdir -p "$(dirname "$LOG_FILE")"
# echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") POST $TOOL exit=$EXIT_CODE ${COMMAND:0:120}" >> "$LOG_FILE"

# ── NOTIFICAÇÃO ─────────────────────────────────────────────────────────────
# Notificar quando uma ferramenta falhar.

# if [[ -n "$EXIT_CODE" && "$EXIT_CODE" != "0" ]]; then
#   osascript -e "display notification \"$TOOL falhou (exit $EXIT_CODE)\" with title \"Claude Code\"" 2>/dev/null || true
# fi

exit 0

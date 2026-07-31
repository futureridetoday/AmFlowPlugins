#!/usr/bin/env bash
# Hook: PreToolUse
# Executa antes de qualquer chamada de ferramenta.
# Recebe JSON via stdin com informações sobre a ferramenta e seus argumentos.
# Usos: bloquear ferramentas perigosas, injetar contexto, registrar auditoria.

set -euo pipefail

INPUT=$(cat)

# Extrair campos em uma única chamada ao Python
eval "$(echo "$INPUT" | python3 -c "
import sys, json, shlex
d = json.load(sys.stdin)
tool = d.get('tool', '')
command = d.get('input', {}).get('command', '').replace('\n', ' ')
print('TOOL=' + shlex.quote(tool))
print('COMMAND=' + shlex.quote(command))
" 2>/dev/null || echo "TOOL='' COMMAND=''")"

# ── BLOQUEAR ────────────────────────────────────────────────────────────────
# Exit 2 bloqueia a execução e exibe a mensagem de erro ao usuário.

# if [[ "$TOOL" == "Bash" ]] && echo "$COMMAND" | grep -qE "rm -rf|drop table|DROP TABLE"; then
#   echo "Operação destrutiva bloqueada: requer confirmação manual." >&2
#   exit 2
# fi

# ── INJETAR CONTEXTO ────────────────────────────────────────────────────────
# Texto escrito no stdout é injetado no contexto do Claude antes da ferramenta executar.

# echo "Contexto adicional antes de executar $TOOL"

# ── AUDITORIA ───────────────────────────────────────────────────────────────

# LOG_FILE="${HOME}/.claude/logs/tool-use.log"
# mkdir -p "$(dirname "$LOG_FILE")"
# echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") PRE  $TOOL ${COMMAND:0:120}" >> "$LOG_FILE"

exit 0

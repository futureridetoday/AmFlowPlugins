#!/usr/bin/env bash
# guard.sh — hook Stop hard-memory-guard (WO-14)
#
# Garante que arquivos de Hard Memory usados na sessão sejam escritos antes do
# encerramento. Se um arquivo de memória referenciado na sessão não foi
# modificado desde o início dela, bloqueia o Stop com instrução para executar
# o protocolo de escrita da skill hard-memory.
#
# Zero dependências além de bash + utilitários POSIX. Falha sempre em noop —
# um guard quebrado nunca pode impedir o encerramento da sessão.

set -u

INPUT=$(cat 2>/dev/null) || exit 0

# Evita loop infinito: se este Stop já veio de um bloqueio anterior do próprio
# hook, deixa encerrar
printf '%s' "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && exit 0

TRANSCRIPT=$(printf '%s' "$INPUT" |
  grep -o '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 |
  sed 's/^[^:]*:[[:space:]]*"//; s/"$//')
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0

# Sessões que não tocaram em Hard Memory: noop
grep -q 'hard-memory/' "$TRANSCRIPT" 2>/dev/null || exit 0

# Início da sessão: timestamp da primeira entrada do transcript
FIRST_TS=$(head -c 8192 "$TRANSCRIPT" |
  grep -o '"timestamp"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 |
  sed 's/^[^:]*:[[:space:]]*"//; s/"$//')
[ -n "$FIRST_TS" ] || exit 0

ISO_BASE="${FIRST_TS%%.*}"
ISO_BASE="${ISO_BASE%Z}"
SESSION_START=$(date -u -j -f '%Y-%m-%dT%H:%M:%S' "$ISO_BASE" +%s 2>/dev/null) ||
  SESSION_START=$(date -u -d "$ISO_BASE" +%s 2>/dev/null) || exit 0

file_mtime() {
  stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0
}

# Candidatos: memórias do projeto atual (cwd do hook) e globais, exceto archives
STALE=""
for f in .claude/hard-memory/*.md "$HOME"/.claude/hard-memory/*.md; do
  [ -f "$f" ] || continue
  case "$f" in *.archive.md) continue ;; esac
  # Só cobra arquivos que a sessão de fato referenciou
  grep -q "$(basename "$f")" "$TRANSCRIPT" 2>/dev/null || continue
  if [ "$(file_mtime "$f")" -lt "$SESSION_START" ]; then
    STALE="$STALE $f"
  fi
done

[ -n "$STALE" ] || exit 0

STALE_LIST=$(printf '%s' "$STALE" | sed 's/^ //; s/ /, /g')
cat <<EOF
{"decision": "block", "reason": "Hard Memory: o(s) arquivo(s) de memória $STALE_LIST não foi(ram) atualizado(s) nesta sessão. Execute o protocolo de escrita da skill hard-memory (consolidar estado nas seções, atualizar frontmatter updated/sessions) antes de encerrar."}
EOF
exit 0

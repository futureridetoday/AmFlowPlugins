#!/usr/bin/env bash
# guard.sh — hook PreToolUse path-safety (B3)
#
# Barreira determinística para Write/Edit/MultiEdit: rejeita travessia (../ ou
# /..) e escrita em alvos sensíveis enumerados — chaves, perfis de shell, hooks
# de git e settings do Claude —, ANTES da escrita. Substitui validate-bundle.sh
# (M5) — o servidor já valida (A5.4), mas o cliente nunca confia só nisso.
#
# Deny-list, não allow-list (D-07). A regra anterior só permitia escrita em
# ~/.claude/ e <cwd>/.claude/, o que impedia qualquer usuário com o Worker
# instalado de criar arquivo no próprio projeto. Qualquer path que não seja
# travessia nem alvo enumerado é permitido.
#
# Universal: se aplica a qualquer escrita da sessão com o Worker ativo, não só
# durante install/update — decisão deliberada (M5 cobre prompt-injection, não
# só travessia dentro de um path de bundle).
#
# Diferente do hard-memory-guard (fail-open — "nunca pode impedir o
# encerramento", é lembrete): este hook é fail-closed — qualquer ambiguidade
# ao interpretar o input bloqueia a escrita, nunca libera. Zero dependências
# além de bash + POSIX (grep/sed) — sem jq, Python ou Node. Não é mais a
# restrição "native-only" do Worker (revogada — language-policy.md): é que
# este hook roda no Claude Code CLI local, onde Python não é garantido (D-13).

set -u

deny() {
  local escaped
  escaped=$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g')
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"path-safety: %s"}}' "$escaped"
  exit 0
}

INPUT=$(cat 2>/dev/null) || deny "falha ao ler o input do hook."

# Extrai um campo string simples do JSON via grep+sed (sem jq — D10). Um
# valor legítimo (path de bundle, kebab-case) nunca contém backslash; se o
# match cru tiver um, é sinal de aspas escapadas (\") que este parser
# simplificado não interpreta corretamente — [^"]* pararia no primeiro
# caractere " literal, mesmo escapado, truncando o valor. Em vez de arriscar
# extrair um prefixo truncado que passe no check de prefixo por acaso
# enquanto o path real (o que o Write de verdade recebe) escapa de .claude/
# na parte não vista, recusa (fail-closed) sempre que houver ambiguidade.
extract_field() {
  local raw
  raw=$(printf '%s' "$INPUT" | grep -o "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1)
  [ -n "$raw" ] || return 1
  case "$raw" in *'\'*) return 1 ;; esac
  printf '%s' "$raw" | sed 's/^[^:]*:[[:space:]]*"//; s/"$//'
}

FILE_PATH=$(extract_field file_path) || deny "não foi possível determinar o file_path com segurança — escrita bloqueada."
[ -n "$FILE_PATH" ] || deny "file_path vazio."

# Path relativo não é resolvível sem confiar no cwd, e a deny-list casa prefixo
# absoluto — recusa, como a allow-list anterior já fazia por construção. Cobre
# também o til não expandido (~/.ssh/...), que não começa em /.
case "$FILE_PATH" in
  /*) ;;
  *) deny "file_path não é absoluto ($FILE_PATH) — escrita bloqueada." ;;
esac

# Normaliza `//` e `/./` antes de casar: são o mesmo arquivo escrito de outro
# jeito, e uma deny-list que compara texto cru é derrotada por dois caracteres
# ($HOME/./.ssh/x). Itera porque uma passada de sed não reescreve o texto que
# ela mesma produziu — `/a/././b` só vira `/a/b` na segunda.
while :; do
  ANTERIOR=$FILE_PATH
  FILE_PATH=$(printf '%s' "$FILE_PATH" | sed 's|//*|/|g; s|/\./|/|g')
  [ "$FILE_PATH" = "$ANTERIOR" ] && break
done

case "$FILE_PATH" in
  *'../'*|*'/..'|*'/../'*)
    deny "path traversal detectado em $FILE_PATH"
    ;;
esac

case "$FILE_PATH" in
  "$HOME/.ssh/"*|"$HOME/.aws/"*|"$HOME/.gnupg/"* \
    |"$HOME/.zshrc"|"$HOME/.bashrc"|"$HOME/.profile" \
    |*'/.claude/settings.json'|*'/.claude/settings.local.json' \
    |*'/.git/hooks/'*)
    deny "escrita bloqueada em alvo sensível ($FILE_PATH) pelo hook path-safety do plugin Worker — para desabilitar: claude plugin uninstall amflow-worker@amflow"
    ;;
  *) exit 0 ;;
esac

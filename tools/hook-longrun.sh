#!/usr/bin/env bash
# Hook do Claude Code para execuções longas (F4).
#  PreCompact            → systemMessage: "salve state.md/progress.md"
#  SessionStart(compact) → additionalContext: "releia goal → state → plan antes de agir"
# Só fala se o projeto atual tiver longrun/*/state.md sem "concluído". Silencioso no resto.
set -uo pipefail
entrada=$(cat)
ev=$(printf '%s' "$entrada" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("hook_event_name",""))' 2>/dev/null)
cwd=$(printf '%s' "$entrada" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("cwd",""))' 2>/dev/null)
[ -d "$cwd" ] || exit 0
raiz=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || echo "$cwd")

ativas=()
for s in "$raiz"/longrun/*/state.md; do
  [ -f "$s" ] || continue
  grep -qi "concluído\|concluido" "$s" || ativas+=("${s#"$raiz"/}")
done
[ ${#ativas[@]} -eq 0 ] && exit 0
lista=$(printf '%s, ' "${ativas[@]}"); lista=${lista%, }

if [ "$ev" = PreCompact ]; then
  msg="Execução longa ativa ($lista): a compactação vai resumir o histórico. Garanta que state.md e progress.md estão atualizados."
  python3 -c 'import json,sys; print(json.dumps({"systemMessage": sys.argv[1]}, ensure_ascii=False))' "$msg"
else
  ctx="EXECUÇÃO LONGA ATIVA neste projeto ($lista). O contexto acabou de ser compactado: antes de qualquer ação, releia goal.md → state.md → plan.md e as últimas linhas de progress.md e failures.md dessa pasta, e continue do primeiro item pendente sem reabrir o que já está feito."
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": sys.argv[1]}}, ensure_ascii=False))' "$ctx"
fi

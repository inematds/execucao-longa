#!/usr/bin/env bash
# Cria longrun/<AAAA-MM-DD>-<slug>/ num projeto a partir dos templates.
# Uso: tools/novo-longrun.sh <pasta-do-projeto> <slug>
set -euo pipefail
[ $# -eq 2 ] || { echo "uso: $0 <pasta-do-projeto> <slug>" >&2; exit 1; }
proj=$1; slug=$2
tpl="$(cd "$(dirname "$0")/.." && pwd)/templates"
[ -d "$proj" ] || { echo "projeto não existe: $proj" >&2; exit 1; }
dir="$proj/longrun/$(date +%F)-$slug"
[ -e "$dir" ] && { echo "já existe: $dir" >&2; exit 1; }
mkdir -p "$dir"
cp "$tpl"/{goal,plan,state,progress,failures,decisions}.md "$dir/"
sed -i "s/<slug>/$slug/; s/AAAA-MM-DD HH:MM/$(date '+%F %H:%M')/" "$dir/goal.md"
echo "criado: $dir"
echo "próximo: preencher $dir/goal.md (critérios nível 3+) e colar templates/prompt-goal-codex.md no /goal"

#!/usr/bin/env bash
# Laço externo de uma execução longa headless (receita §5.2 do plano).
# Cada ciclo = 1 `codex exec` (ou `claude -p`) com teto de tempo e memória; quem decide continuar
# é o TESTE, não o agente. Trava com flock, devolve testes protegidos, para por estagnação.
#
# Uso: tools/loop-longrun.sh <pasta-longrun>
# Config em <pasta-longrun>/loop.env:
#   TESTE_RAPIDO="pytest -q -m 'not real'"   # roda a cada ciclo
#   TESTE_FINAL="pytest -q"                   # passou = concluído
#   PROTEGIDOS="tests/ pytest.ini"            # se o agente mexer, é revertido e o ciclo conta como falho
#   PERMITIDOS="tools/medir-sessao.py"        # o que entra no commit de checkpoint (além da pasta longrun)
#   MAX_CICLOS=6  MIN_CICLO=20  MEM=8G  ESTAGNACAO=3
#   AGENTE=codex  MODELO=gpt-6-astra          # AGENTE=claude usa `claude -p --max-turns 60`
set -uo pipefail
dir=$(cd "${1:?uso: $0 <pasta-longrun>}" && pwd)
repo=$(git -C "$dir" rev-parse --show-toplevel)
# shellcheck disable=SC1091
source "$dir/loop.env"
: "${TESTE_RAPIDO:?} ${TESTE_FINAL:?} ${PROTEGIDOS:?} ${PERMITIDOS:?}"
MAX_CICLOS=${MAX_CICLOS:-6}; MIN_CICLO=${MIN_CICLO:-20}; MEM=${MEM:-8G}; ESTAGNACAO=${ESTAGNACAO:-3}
AGENTE=${AGENTE:-codex}; MODELO=${MODELO:-gpt-6-astra}
CODEX=${CODEX_BIN:-$HOME/.npm-global/bin/codex}

exec 9>"$dir/.loop.lock"
flock -n 9 || { echo "outro loop já roda nesta pasta" >&2; exit 3; }
cd "$repo"

log() { echo "$(date '+%F %T') $*" | tee -a "$dir/loop.log"; }
passados() { bash -c "$1" 2>&1 | grep -oE '[0-9]+ passed' | tail -1 | grep -oE '[0-9]+' || echo 0; }

melhor=$(passados "$TESTE_RAPIDO"); sem_avanco=0
log "início: rápido=$melhor passed · agente=$AGENTE · teto ${MAX_CICLOS}x${MIN_CICLO}min · mem $MEM"

for ((i = 1; i <= MAX_CICLOS; i++)); do
  log "ciclo $i: começa"
  if [ "$AGENTE" = claude ]; then
    cmd=(claude -p --max-turns 60 --permission-mode acceptEdits)
  else
    cmd=("$CODEX" exec -m "$MODELO" -s workspace-write --skip-git-repo-check -C "$repo" -)
  fi
  t0=$(date +%s)
  timeout "${MIN_CICLO}m" systemd-run --user --scope -q -p MemoryMax="$MEM" "${cmd[@]}" \
    < "$dir/prompt.md" > "$dir/ciclo-$i.log" 2>&1
  rc=$?; log "ciclo $i: agente saiu rc=$rc em $(( $(date +%s) - t0 ))s"

  # shellcheck disable=SC2086
  if ! git diff --quiet -- $PROTEGIDOS || [ -n "$(git ls-files --others --exclude-standard -- $PROTEGIDOS)" ]; then
    log "ciclo $i: agente mexeu em arquivo protegido → revertido, ciclo falho"
    git checkout -- $PROTEGIDOS; git clean -fdq -- $PROTEGIDOS
    echo "| $(date '+%F %T') | ciclo $i alterou $PROTEGIDOS | revertido pelo loop | - |" >> "$dir/failures.md"
    sem_avanco=$((sem_avanco + 1))
  else
    agora=$(passados "$TESTE_RAPIDO")
    log "ciclo $i: rápido=$agora passed (melhor antes: $melhor)"
    if [ "$agora" -gt "$melhor" ]; then melhor=$agora; sem_avanco=0; else sem_avanco=$((sem_avanco + 1)); fi
  fi

  # shellcheck disable=SC2086
  git add -- "$dir" $PERMITIDOS 2>/dev/null
  if ! git diff --cached --quiet; then
    git commit -qm "longrun $(basename "$dir"): checkpoint ciclo $i" && log "ciclo $i: checkpoint commitado"
  fi

  if bash -c "$TESTE_FINAL" > "$dir/teste-final.log" 2>&1; then
    log "CONCLUÍDO no ciclo $i: teste final passou ($(grep -oE '[0-9]+ passed' "$dir/teste-final.log" | tail -1))"
    exit 0
  fi
  if [ "$sem_avanco" -ge "$ESTAGNACAO" ]; then
    log "PARADO: $ESTAGNACAO ciclos sem avanço mensurável — ver failures.md"
    exit 2
  fi
done
log "PARADO: teto de $MAX_CICLOS ciclos atingido sem passar o teste final"
exit 1

# FALHAS — execucao-longa (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-15 | `hook-longrun` calculava a % sobre 1 milhão, mas o Claude Code compacta o Opus 5.5 entre 200 e 575 mil: as faixas de 70/85% dispararam 2 vezes em 8 dias; e o pedido de handoff pós-compactação virou arquivo em só 17 de 84 casos | % sobre o teto `LONGRUN_TETO`=225 mil + conferência do arquivo na transcrição com até 2 cobranças | infra + prompt |
| 2026-10-05 | `loop-longrun.sh` parou o atende-clinica por "3 ciclos sem avanço" com 20→43→63 testes passando: com `pipefail`, `passados()` imprimia "N\n0" quando o pytest falhava e o `-gt` quebrava | capturar em variável e `echo "${n:-0}"` | infra |
| 2026-10-05 | `vigia.py` (timer de 10 min) disparava `notify-send -u critical` "Execução longa": pop-up que não some e acumulava no topo das telas RDP (ociosa repetindo de hora em hora) | `notify-send` só com `--desktop` (opt-in); o alerta continua em `alertas.log` | prompt |
| 2026-10-01 | `pkill -f "<padrão>"` no mesmo comando que continha o padrão matou o próprio shell (exit 144) | Guardrail 4 do plano já existia: matar por PID ou rodar o pkill em comando separado | prompt |
| 2026-10-01 | `codex exec "…"` sem fechar stdin ficou esperando entrada até o timeout de 200 s | Guardrail da §5.2 já existia: sempre `< /dev/null` ou prompt por arquivo (`- < prompt.md`) | prompt |

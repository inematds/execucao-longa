# FALHAS — execucao-longa (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-01 | `pkill -f "<padrão>"` no mesmo comando que continha o padrão matou o próprio shell (exit 144) | Guardrail 4 do plano já existia: matar por PID ou rodar o pkill em comando separado | prompt |
| 2026-10-01 | `codex exec "…"` sem fechar stdin ficou esperando entrada até o timeout de 200 s | Guardrail da §5.2 já existia: sempre `< /dev/null` ou prompt por arquivo (`- < prompt.md`) | prompt |

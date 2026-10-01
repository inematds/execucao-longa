# Plano

## Estratégia atual
Implementação e verificações encerradas: 12 testes rápidos e 14 completos passaram.
Biblioteca padrão; memória proporcional à maior linha e aos registros mínimos dos turnos, sem acumular conteúdo das sessões.

## Próximos passos
1. O loop externo reconhece `concluído` no state.md e encerra novos ciclos de implementação.
2. O loop externo realiza o checkpoint/commit dos arquivos autorizados; preservar a alteração prévia em templates/AGENTS-long-run.md.
3. Em eventual novo requisito ou regressão, ler goal → state → plan → registros e repetir os comandos documentados no state.md.

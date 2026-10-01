# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-01 14:22:32 -0300 | JSONL em modo binário, uma linha por vez; contar bytes efetivamente lidos; guardar apenas contadores por id Claude e curva Codex quando solicitada | Suporta sessões grandes sem reter conteúdo; último usage preserva timestamp e compactações iniciais | Carregar arquivo inteiro ou guardar mensagens completas |
| 2026-10-01 14:22:32 -0300 | --por-turno exige --json; um arquivo retorna lista de pontos, vários retornam listas na ordem dos arquivos | Contrato dos testes e saída inequívoca; resumo sem timestamp válido usa duração 0 | Misturar curva e resumo no mesmo objeto |

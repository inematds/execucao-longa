# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-01 20:48:17 -0300 | FTS5 com metadados não indexados e tabela de checkpoints por arquivo; transação por arquivo | Persistir offset, linha e cwd e manter atomicidade | Releitura integral de JSONL crescente |
| 2026-10-01 20:48:17 -0300 | Cada termo escapado entre aspas e combinado por AND; conexão somente leitura para buscar | Evitar sintaxe FTS injetada e criação acidental de banco | MATCH direto do usuário |
| 2026-10-01 20:48:17 -0300 | Gzip alterado é relido integralmente; JSONL de mesmo tamanho com mtime diferente também | Detectar substituições e evitar offsets comprimidos inválidos | Retomar gzip alterado por offset |

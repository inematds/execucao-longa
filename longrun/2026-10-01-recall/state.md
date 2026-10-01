# Estado — atualizado 2026-10-01 20:48:17 -0300

## Funciona
concluído

- `tools/recall.py`: indexação SQLite FTS5, extração Codex/Claude, gzip, retomada incremental com projeto/linha/offset persistidos, reindexação de arquivos reduzidos ou substituídos com mesmo tamanho, filtros e busca literal segura, saída JSON/texto e atalho.
- Rápido: 14 passed, 1 deselected (1.43 s); completo: 15 passed, 0 failed, 0 skips (3.27 s).
- Regressão: 12 passed, 2 deselected (0.30 s).
- Verificação sintética: última linha sem newline, idempotência e consultas com aspas, dois-pontos, hífen, OR e asterisco; 6 buscas em 0.001 s em banco pequeno.
- `git diff --exit-code -- tests/ pytest.ini`: vazio. Nenhuma API, rede ou dependência nova; sessões reais acessadas somente pelo teste real, em banco temporário.

## Falta
- Nenhuma implementação pendente nos critérios funcionais; commit fica a cargo do loop externo.
- Alterações paralelas surgiram em docs/, guia/ e tools/faxina-claude-mem.py; não são deste ciclo e não foram editadas por este agente.
- O prefixo de hash informado no goal não coincide com o SHA-256 observado (2efecb451d28c4fe7); os testes estão sem diff no Git e não foram modificados.

## Como retomar
```bash
cd /home/nmaldaner/projetos/execucao-longa
pytest -q -m "not real" tests/test_recall.py
pytest -q tests/test_recall.py
pytest -q tests/test_medir_sessao.py -m "not real"
git diff --exit-code -- tests/ pytest.ini
```
O objetivo está concluído; não indexar sessões reais fora do teste real. Sem commit neste ciclo.

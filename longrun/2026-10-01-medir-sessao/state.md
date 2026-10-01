# Estado — atualizado 2026-10-01 14:22:32 -0300

## Funciona
concluído
- `tools/medir-sessao.py`: detecção Codex/Claude, leitura JSONL linha a linha, duração, tokens/cache, compactações, modelos, bytes de ferramentas, JSON e texto, curva por turno e múltiplos arquivos.
- Claude: deduplicação por id com último usage e timestamp/compactações da primeira ocorrência.
- `pytest -q -m "not real"`: 12 passed, 2 deselected (0,35 s).
- `pytest -q`: 14 passed (8,92 s), 0 failed, 0 skips; inclui sessão Codex de 1,84 GB e Claude de 17 h.
- Regressão: `python3 tools/medicao/cx.py | head -1` e `python3 tools/medicao/cc.py | head -1` finalizaram com código 0; Codex reportou 10303 linhas/13 compactações; Claude reportou 5695 sessões/3,88 GB.
- `git diff --exit-code -- tests/ pytest.ini`: vazio, código 0.

## Falta
- Nenhuma implementação ou validação pendente neste ciclo. Commit fica a cargo do loop externo, conforme solicitado.
- A alteração prévia em `templates/AGENTS-long-run.md` não foi feita nem modificada neste ciclo.

## Como retomar (comandos exatos)
```bash
cd /home/nmaldaner/projetos/execucao-longa
python3 tools/medir-sessao.py tests/fixtures/codex_mini.jsonl --json
python3 tools/medir-sessao.py tests/fixtures/claude_mini.jsonl --json --por-turno
pytest -q -m "not real"
pytest -q
git diff --exit-code -- tests/ pytest.ini
```

Critérios atendidos; não reabrir implementação sem novo requisito ou falha observada.

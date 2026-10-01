# Goal — medir-sessao (piloto F1, que entrega a F2)

- **Início:** 2026-10-01 · **Agente:** `codex exec` (gpt-6-astra, assinatura) em loop headless — receita §5.2 do plano
- **Tetos:** 6 ciclos · 20 min por ciclo · memória 8G por ciclo

## Resultado
`tools/medir-sessao.py` lê um ou mais JSONL de sessão (Codex ou Claude Code) e mostra duração, compactações, tokens, cache ratio, bytes de saída de ferramenta e modelos — resumo em texto, `--json` e curva `--por-turno`.

## Especificação
- Uso: `python3 tools/medir-sessao.py <arquivo.jsonl> [mais.jsonl ...] [--json] [--por-turno]`. Só biblioteca padrão do Python. Leitura em streaming (arquivos de 2 GB).
- Detecta a fonte: **codex** se houver linhas com `type` em `session_meta`/`turn_context`/`response_item`/`event_msg`; **claude** se houver `type` `user`/`assistant` com `message`. Linhas que não são JSON são contadas em `linhas` e ignoradas no resto.
- `--json` com 1 arquivo → objeto; com vários → lista na mesma ordem. Campos: `fonte, arquivo, bytes, linhas, inicio, fim, duracao_s, compactacoes, input_tokens, cached_tokens, cache_write_tokens, output_tokens, cache_ratio, bytes_saida_ferramenta, modelos, turnos`.
- `inicio`/`fim`: primeiro/último `timestamp` (string original). `duracao_s`: inteiro, segundos truncados.
- **Codex**: tokens = `total_token_usage` do último evento `event_msg` com `payload.type == "token_count"` e `info` não nulo (`input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`); `cache_ratio = cached/input`; `turnos` = nº desses eventos com `info`; `compactacoes` = nº de linhas `type == "compacted"`; `modelos` = `payload.model` dos `turn_context`, ordenados e sem repetição; `bytes_saida_ferramenta` = soma dos `payload.output` de `response_item` com `payload.type` em `function_call_output`/`custom_tool_call_output` (string → bytes UTF-8; outro tipo → bytes de `json.dumps(x, ensure_ascii=False)`).
- **Claude**: mensagens `assistant` com `message.usage`, **deduplicadas por `message.id`** (usage da última ocorrência, timestamp da primeira). `input_tokens = input + cache_read + cache_creation`; `cached_tokens = cache_read`; `cache_write_tokens = cache_creation`; `cache_ratio = cached/input_tokens`; `turnos` = nº de ids; `compactacoes` = linhas `type == "system"` e `subtype == "compact_boundary"`; `modelos` = `message.model` das mensagens com usage, sem `<synthetic>`; `bytes_saida_ferramenta` = soma do `content` dos blocos `tool_result` em mensagens `user` (mesma regra string/json).
- `--por-turno` (com `--json`): lista `{i, timestamp, input, cached, ratio, compactacoes}` — Codex usa `last_token_usage` de cada `token_count`; Claude usa cada id na ordem da primeira ocorrência; `input` do Claude é o total (input+cache_read+cache_creation); `compactacoes` = quantas aconteceram até aquele ponto; `ratio` = cached/input (0.0 se input 0).
- Sem `--json`: resumo legível com a fonte, `compactações: N` e `cache: XX.X%`.
- Arquivo inexistente: sai com código ≠ 0 e "não encontrado" no stderr.

## Critérios de pronto (verificáveis)

**Função**
- [ ] `pytest -q` → todos passam (12 rápidos + 2 com sessões reais), 0 falhas, 0 skips nesta máquina

**Regressão**
- [ ] `python3 tools/medicao/cx.py | head -1` e `python3 tools/medicao/cc.py | head -1` continuam rodando (não mexer em `tools/medicao/`)

**Limite**
- [ ] `git diff --exit-code -- tests/ pytest.ini` → vazio (testes congelados; hash inicial `3ae1ba7975508cba`)
- [ ] só criar/alterar `tools/medir-sessao.py` e os arquivos desta pasta `longrun/`

**Teste rápido por ciclo**: `pytest -q -m "not real"`
**Teste completo no final**: `pytest -q`

## Restrições
- só pela assinatura; nenhuma API; nenhuma dependência nova
- não mexer em: `tests/`, `pytest.ini`, `tools/medicao/`, `docs/`, `guia/`, `templates/`

## Portões humanos (parar e perguntar)
- qualquer mudança fora de `tools/medir-sessao.py` e desta pasta

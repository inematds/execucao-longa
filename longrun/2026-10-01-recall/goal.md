# Goal — recall (F8: busca no histórico)

- **Início:** 2026-10-01 · **Agente:** `codex exec` (gpt-6-astra, assinatura) em loop headless — `tools/loop-longrun.sh`
- **Tetos:** 6 ciclos · 20 min por ciclo · memória 8G por ciclo

## Resultado
`tools/recall.py` mantém um índice SQLite FTS5 das transcrições do Codex e do Claude Code (sem saída de ferramenta) e busca nele em menos de 1 s, com filtros de projeto, fonte, papel e data.

## Especificação
- Só biblioteca padrão do Python (`sqlite3` com FTS5, `gzip`, `json`, `argparse`). Leitura em streaming.
- Banco: `$RECALL_DB` ou `~/.local/share/execucao-longa/recall.db`. Tokenizer FTS5 `unicode61 remove_diacritics 2` (busca sem acento acha com acento).
- **`recall.py indexar [--codex DIR] [--claude DIR] [--arquivo DIR]`** — padrões: `~/.codex/sessions`, `~/.claude/projects`, `~/.local/share/execucao-longa/arquivo`. Varre `*.jsonl` recursivamente nas duas primeiras; em `--arquivo`, varre `*.jsonl.gz` e a fonte é o 1º diretório do caminho relativo (`codex/…` ou `claude/…`).
  - **Incremental:** guarda por arquivo o tamanho, o mtime e o byte já lido. Arquivo maior → lê só o resto. Arquivo menor que o já lido (reescrito) → apaga os trechos dele e reindexa do zero. `.gz` sem mudança de tamanho/mtime → pula. Rodar duas vezes seguidas não duplica nada.
  - Linhas que não são JSON são ignoradas (mas contam para o número da linha).
  - Ao terminar, imprime quantos arquivos e trechos novos.
- **O que vira trecho** (`papel` ∈ `user`, `assistant`, `ferramenta`):
  - **Codex:** `response_item` com `payload.type == "message"` e `role` `user`/`assistant`: junta os textos dos blocos `input_text`/`output_text`. Ignora `role == "developer"` e textos de usuário que começam com `# AGENTS.md instructions`, `<environment_context>`, `<user_instructions>` ou `<INSTRUCTIONS>`. `response_item` `function_call`/`custom_tool_call` → papel `ferramenta`, texto = `nome + " " + (arguments ou input)[:300]`. Ignora `*_output`, `reasoning`, `event_msg` e linhas `type == "compacted"`. Projeto = basename do último `cwd` visto em `session_meta`/`turn_context` (atualiza no meio da sessão).
  - **Claude Code:** `type == "user"`: `message.content` string, ou blocos `type == "text"`; ignora `isMeta == true`, conteúdo que começa com `<system-reminder>`, `<command-`, `<local-command` e blocos `tool_result`. `type == "assistant"`: blocos `text` → papel `assistant`; blocos `tool_use` → papel `ferramenta`, texto = `nome + " " + json.dumps(input)[:300]`; ignora `thinking`. Projeto = basename do `cwd` da linha.
  - Data = `timestamp` da linha (string ISO). Linha = número da linha no arquivo (1-based).
- **`recall.py buscar TERMOS [--projeto P] [--fonte codex|claude] [--papel user|assistant|ferramenta] [--desde AAAA-MM-DD] [-n 20] [--json]`** — cada termo vira um token entre aspas (o texto do usuário nunca quebra a sintaxe do FTS5); todos os termos precisam aparecer. Ordena por relevância (bm25) e depois data mais recente. `--json` → lista de objetos `{data, fonte, projeto, papel, trecho, arquivo, linha}` (`trecho` = até ~300 caracteres em volta do termo; `arquivo` = caminho absoluto; `linha` = int). Sem `--json`: uma linha por resultado com data, fonte, projeto, papel, trecho e `arquivo:linha`.
- `recall.py TERMOS` sem subcomando = `buscar`.
- Sem índice criado: sai com código ≠ 0 e mensagem citando `indexar` no stderr.

## Critérios de pronto (verificáveis)

**Função**
- [ ] `pytest -q tests/test_recall.py` → 15 passed (14 rápidos + 1 com sessões reais), 0 falhas, 0 skips nesta máquina

**Regressão**
- [ ] `pytest -q tests/test_medir_sessao.py -m "not real"` → 12 passed

**Limite**
- [ ] `git diff --exit-code -- tests/ pytest.ini` → vazio (hash inicial dos testes do recall `588aab036a5067a8`)
- [ ] só criar/alterar `tools/recall.py` e os arquivos desta pasta `longrun/`
- [ ] nada de rede, nenhuma API, nenhuma dependência nova

**Teste rápido por ciclo**: `pytest -q -m "not real" tests/test_recall.py`
**Teste completo no final**: `pytest -q tests/test_recall.py`

## Restrições
- só pela assinatura; não mexer em `tests/`, `pytest.ini`, `tools/` (exceto `tools/recall.py`), `docs/`, `guia/`, `templates/`
- não indexar as sessões reais da máquina durante o trabalho (só o teste `real` faz isso, num banco temporário)

## Portões humanos (parar e perguntar)
- qualquer mudança fora de `tools/recall.py` e desta pasta

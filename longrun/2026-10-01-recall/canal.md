# Canal — recall (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 2026-10-01 20:40 · fato · Codex JSONL: mensagens úteis = `response_item` com `payload.type=message` e role user/assistant; role `developer` e textos que começam com "# AGENTS.md instructions" / "<environment_context>" / "<user_instructions>" são injeção do sistema. Linha `type=compacted` repete o histórico (`replacement_history`) → ignorar. Projeto = basename do `cwd` em `session_meta` e `turn_context`.
- 2026-10-01 20:40 · fato · Claude JSONL: cada linha tem `cwd`; mensagens `assistant` repetem o mesmo `message.id` por bloco de conteúdo; `user` com `isMeta`, `<system-reminder>` e blocos `tool_result` não são fala do usuário.
- 2026-10-01 20:40 · armadilha · SQLite FTS5: texto do usuário vai direto no MATCH e quebra com `-`, `"`, `:`; quotar cada termo. Para achar "migracao" em "migração": tokenizer `unicode61 remove_diacritics 2`.
- 2026-10-01 20:40 · armadilha · `codex exec` sem `< /dev/null` trava; `pkill -f` com o padrão no mesmo comando mata o próprio shell (FALHAS.md).
- 2026-10-01 20:40 · aprendizado · O aviso de faixa chega uma chamada de ferramenta depois (transcrição gravada com atraso). Testes do piloto anterior: oráculo calculado à parte antes de rodar o agente.
- 2026-10-01 20:40 · onde · Índice: `~/.local/share/execucao-longa/recall.db` (env RECALL_DB). Sessões arquivadas: `~/.local/share/execucao-longa/arquivo/<fonte>/...jsonl.gz`.

## Execução longa (/goal, loop, objetivo de horas) — método em ~/projetos/execucao-longa

- **Antes de começar:** `~/projetos/execucao-longa/tools/novo-longrun.sh <projeto> <slug>` cria `longrun/<data>-<slug>/` (goal, plan, state, progress, failures, decisions, canal). Critério de pronto no `goal.md` em **nível 3+**: `comando → saída esperada`, cobrindo função, regressão e limite, sem atalho possível (contagem mínima, testes congelados, validador).
- **Durante:** releia goal → state → plan → canal após toda compactação ou retomada; registre cedo no `canal.md` (só acrescentar) fatos, aprendizados, glossário e armadilhas; teste cada mudança; commit a cada checkpoint; continue enquanto houver próxima ação útil e segura.
- **Parar e chamar o humano:** 3 ciclos sem avanço mensurável; o mesmo plano de fechamento repetido sem fechar ou item já feito reaberto (contexto degradou); crédito/API, ação irreversível ou externa, credencial ausente, decisão de negócio.
- **Faixas de contexto** (no Claude Code o hook avisa uma vez cada; no Codex, acompanhe o % em `/status`): ~50% → registrar no `canal.md`; ~70% → atualizar estado e pedir `/compact`; ~85% ou 3ª compactação → `/session-handoff` + sessão nova + `/prime`.
- **Headless:** `~/projetos/execucao-longa/tools/loop-longrun.sh <pasta-longrun>` (flock, timeout, MemoryMax, testes protegidos, parada por estagnação). Medir: `tools/medir-sessao.py <jsonl>`.
- Tetos sempre: timeout, memória (`systemd-run --user --scope -p MemoryMax=`), saída de ferramenta curta.
- **Histórico:** `recall "termo" [--projeto X] [--fonte codex|claude] [--desde AAAA-MM-DD]` busca em tudo o que já foi dito com o Codex e o Claude nesta máquina (índice reindexado de hora em hora) — use antes de perguntar ao usuário algo que pode já ter sido decidido.

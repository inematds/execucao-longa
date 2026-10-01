## Execução longa (/goal, loop, objetivo de horas) — método em ~/projetos/execucao-longa

- **Antes de começar:** `~/projetos/execucao-longa/tools/novo-longrun.sh <projeto> <slug>` cria `longrun/<data>-<slug>/` (goal, plan, state, progress, failures, decisions). Critério de pronto no `goal.md` em **nível 3+**: `comando → saída esperada`, cobrindo função, regressão e limite, sem atalho possível (contagem mínima, testes congelados, validador).
- **Durante:** releia goal → state → plan após toda compactação ou retomada; teste cada mudança; commit a cada checkpoint; continue enquanto houver próxima ação útil e segura.
- **Parar e chamar o humano:** 3 ciclos sem avanço mensurável; o mesmo plano de fechamento repetido sem fechar ou item já feito reaberto (contexto degradou); crédito/API, ação irreversível ou externa, credencial ausente, decisão de negócio.
- **3ª compactação na mesma sessão** = handoff + sessão nova. Compactar à mão entre 60 e 80%.
- **Headless:** `~/projetos/execucao-longa/tools/loop-longrun.sh <pasta-longrun>` (flock, timeout, MemoryMax, testes protegidos, parada por estagnação). Medir: `tools/medir-sessao.py <jsonl>`.
- Tetos sempre: timeout, memória (`systemd-run --user --scope -p MemoryMax=`), saída de ferramenta curta.

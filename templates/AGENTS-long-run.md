## LONG-RUN MODE (trecho para AGENTS.md / CLAUDE.md)

Para objetivos longos (/goal ou execução contínua):
- estado em `longrun/<data>-<slug>/` (goal, plan, state, progress, failures, decisions) — modelos em ~/projetos/execucao-longa/templates;
- releia goal → state → plan após compactação ou retomada;
- teste cada mudança; commit a cada checkpoint;
- continue enquanto houver próxima ação útil e segura; 3 ciclos sem avanço = parar e registrar;
- portões humanos: crédito/API, irreversível/externo, credencial, decisão de negócio;
- tetos sempre: timeout, memória (systemd-run), saída de ferramenta curta.

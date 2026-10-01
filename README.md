# Execução Longa

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Execução Longa](guia/assets/banner.jpg)](https://inematds.github.io/execucao-longa/guia/)

Kit para deixar um agente (Codex `/goal` ou Claude Code `/goal`) trabalhando por horas **sem perder o rumo**: objetivo com prova de pronto, estado em arquivos e regras de parada.

📖 Guia visual: **https://inematds.github.io/execucao-longa/guia/**

## Em 5 passos

**1. Crie a pasta da execução no seu projeto**
```bash
~/projetos/execucao-longa/tools/novo-longrun.sh ~/projetos/meu-projeto meu-objetivo
# → meu-projeto/longrun/2026-10-01-meu-objetivo/ com goal, plan, state, progress, failures, decisions
```

**2. Preencha o `goal.md`** — resultado em uma frase + critérios no formato `comando → saída esperada`, cobrindo:
- **função** (faz o que devia) · **regressão** (não quebrou o resto) · **limite** (não mexeu onde não devia)
- mínimo **nível 3**: não dá para cumprir por atalho (ex.: "0 falhas **e** ≥ 48 testes **e** `tests/` intocado", não só "0 falhas")

**3. Inicie o goal**
- Codex: `codex` → cole `templates/prompt-goal-codex.md` preenchido em `/goal`
- Claude Code: `/goal` com `templates/prompt-goal-claude.md` — a prova tem que **aparecer na saída** (o avaliador só lê a conversa)

**4. Acompanhe sem interromper** — `/goals`, `/goal pause|resume`, `/side` (Codex). Pare e intervenha se:
- 3 ciclos sem avanço mensurável;
- o agente repete "vou terminar e commitar" sem terminar, ou reabre item já feito (contexto degradou);
- 3ª compactação na mesma sessão → handoff + sessão nova.

**5. Feche e meça** — `state.md` diz "concluído", critérios passam, e:
```bash
python3 ~/projetos/execucao-longa/tools/medicao/cx.py   # Codex: duração, compactações, tokens, cache
python3 ~/projetos/execucao-longa/tools/medicao/cc.py   # Claude Code: cache_read %, duração
```

## Use quando / não use quando

| ✅ Use | ❌ Não use (ou quebre em sessões menores) |
|---|---|
| Um objetivo, testável por comando | Objetivo muda no meio |
| Trabalho local e reversível | Passos pagos/irreversíveis no caminho (viram portão humano) |
| Dá para medir progresso a cada ciclo | Não há como verificar além de "parece bom" |

Muitas tarefas pequenas e um backlog que cresce? Use o **modo fila** (plano §5.4).

## O que tem aqui

| | |
|---|---|
| [`tools/novo-longrun.sh`](tools/novo-longrun.sh) | Cria a pasta `longrun/` de uma execução a partir dos templates |
| [`templates/`](templates/) | `goal.md` (com escala de critérios), `state/plan/progress/failures/decisions.md`, prompts `/goal` e o trecho LONG-RUN para `AGENTS.md`/`CLAUDE.md` |
| [`tools/medicao/`](tools/medicao/) | Scripts que leem os JSONL de sessão (Codex e Claude Code): duração, compactações, tokens, cache |
| [Plano](docs/PLANO-EXECUCAO-LONGA.md) | O método completo: critérios (§3.1), arquivos de estado, receitas por ferramenta, modo fila, guardrails, fases |
| [Pesquisa jul–out/2026](docs/pesquisa-web-2026-10.md) | O que mudou no Codex, Claude Code e outros, com fontes |
| [Pesquisa `/goal`, contexto e fila](docs/pesquisa-goal-contexto-fila-2026-10.md) | Deterioração de contexto, cache entre ciclos, modo fila (Symphony/Linear) |
| [`docs/origem/`](docs/origem/) | Material que originou o projeto |

Status: F0 (método, templates e scripts). Próximas fases no §8 do plano.

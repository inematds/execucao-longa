# Long Runs

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Long Runs](guia/assets/banner-en.jpg)](https://inematds.github.io/execucao-longa/guia/en/)

A kit to keep an agent (Codex `/goal` or Claude Code `/goal`) working for hours **without losing its way**: a goal with proof of done, state in files and stop rules.

📖 Visual guide: **https://inematds.github.io/execucao-longa/guia/en/**

## In 5 steps

**1. Create the run folder in your project**
```bash
~/projetos/execucao-longa/tools/novo-longrun.sh ~/projetos/my-project my-goal
# → my-project/longrun/2026-10-01-my-goal/ with goal, plan, state, progress, failures, decisions
```

**2. Fill in `goal.md`** — the outcome in one sentence + criteria as `command → expected output`, covering:
- **function** (does what it should) · **regression** (did not break the rest) · **limits** (did not touch what it should not)
- at least **level 3**: it cannot be met through a shortcut (e.g. "0 failures **and** ≥ 48 tests **and** `tests/` untouched", not just "0 failures")

**3. Start the goal**
- Codex: `codex` → paste the filled-in `templates/prompt-goal-codex.md` into `/goal`
- Claude Code: `/goal` with `templates/prompt-goal-claude.md` — the proof must **show up in the output** (the evaluator only reads the conversation)

**4. Follow without interrupting** — `/goals`, `/goal pause|resume`, `/side` (Codex). Stop and step in if:
- 3 cycles with no measurable progress;
- the agent keeps saying "I will finish and commit" without finishing, or reopens finished items (context has degraded);
- 3rd compaction in the same session → handoff + fresh session.

**5. Close and measure** — `state.md` says "done", criteria pass, and:
```bash
python3 ~/projetos/execucao-longa/tools/medicao/cx.py   # Codex: duration, compactions, tokens, cache
python3 ~/projetos/execucao-longa/tools/medicao/cc.py   # Claude Code: cache_read %, duration
```

## Use when / don't use when

| ✅ Use | ❌ Don't (or split into smaller sessions) |
|---|---|
| One goal, testable by a command | The goal changes midway |
| Local, reversible work | Paid/irreversible steps on the way (they become human gates) |
| Progress can be measured every cycle | No way to verify beyond "looks good" |

Many small tasks and a growing backlog? Use **queue mode** (plan §5.4).

## What's here

| | |
|---|---|
| [`tools/novo-longrun.sh`](tools/novo-longrun.sh) | Creates a run's `longrun/` folder from the templates |
| [`templates/`](templates/) | `goal.md` (with the criteria scale), `state/plan/progress/failures/decisions.md`, `/goal` prompts and the LONG-RUN snippet for `AGENTS.md`/`CLAUDE.md` |
| [`tools/medicao/`](tools/medicao/) | Scripts that read session JSONL (Codex and Claude Code): duration, compactions, tokens, cache |
| [Plan](docs/PLANO-EXECUCAO-LONGA.md) | The full method: criteria (§3.1), state files, recipes per tool, queue mode, guardrails, phases (in Portuguese) |
| [Research Jul–Oct 2026](docs/pesquisa-web-2026-10.md) | What changed in Codex, Claude Code and others, with sources (in Portuguese) |
| [Research: `/goal`, context and queue](docs/pesquisa-goal-contexto-fila-2026-10.md) | Context rot, cache between cycles, queue mode (Symphony/Linear) (in Portuguese) |
| [`docs/origem/`](docs/origem/) | Source material behind the project |

Status: F0 (method, templates and scripts). Next phases in §8 of the plan.

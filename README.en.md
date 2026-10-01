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

**5. Close and measure** — `state.md` says "done", you run the final test yourself, and:
```bash
python3 ~/projetos/execucao-longa/tools/medir-sessao.py <session.jsonl>             # duration, compactions, tokens, cache
python3 ~/projetos/execucao-longa/tools/medir-sessao.py <session.jsonl> --json --por-turno
```

**Want it to run on its own?** Instead of step 3, put `prompt.md` + `loop.env` in the folder (copy from [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/)) and run `tools/loop-longrun.sh <folder>`. Each cycle is one capped `codex exec`; the test decides whether to continue, and the loop stops on its own (done, stagnation or cap).

## Install once per machine

1. Clone into `~/projetos/execucao-longa`.
2. Paste [`templates/AGENTS-long-run.md`](templates/AGENTS-long-run.md) into your global `CLAUDE.md` and `AGENTS.md` — the agent follows the method without being reminded.
3. In `~/.claude/settings.json`, hook `tools/hook-longrun.sh` to `PreCompact` and `SessionStart` (matcher `compact|resume`): after compacting or resuming, the agent is told to reread its state.
4. Watchdog: copy `tools/systemd/longrun-vigia.*` to `~/.config/systemd/user/` and run `systemctl --user enable --now longrun-vigia.timer` (alerts on stopped or idle runs).
5. Cron jobs that call agents: `flock -n <lock> timeout <cap> <script>`.

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
| [`tools/loop-longrun.sh`](tools/loop-longrun.sh) | Headless loop: `codex exec` cycles with flock, timeout and memory cap; the test decides; stops on stagnation |
| [`tools/medir-sessao.py`](tools/medir-sessao.py) | Measures a session (Codex or Claude): duration, compactions, tokens, cache, tool output, per-turn curve |
| [`tools/hook-longrun.sh`](tools/hook-longrun.sh) | Claude Code hook: reminds to save before compacting and to reread afterwards |
| [`tools/vigia.py`](tools/vigia.py) | Watchdog (timer every 10 min): flags runs that stopped, stopped silently or went idle |
| [`tools/arquivar-sessoes.py`](tools/arquivar-sessoes.py) | Hygiene: report on space used by old sessions; `--aplicar` compresses, `--restaurar` restores |
| [`templates/`](templates/) | `goal.md` (with the criteria scale), `state/plan/progress/failures/decisions.md`, `/goal` prompts and the LONG-RUN snippet for `AGENTS.md`/`CLAUDE.md` |
| [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/) | Real example: the pilot that built `medir-sessao.py` in 1 cycle |
| [Plan](docs/PLANO-EXECUCAO-LONGA.md) | The full method: criteria (§3.1), state files, recipes, queue mode, guardrails, phases and pilot lessons (in Portuguese) |
| [F7 retrospective](docs/experimento-f7-retrospectivo-2026-10.md) | Cache and cost-per-turn curve on 3 real sessions + experiment protocol (in Portuguese) |
| [Research Jul–Oct 2026](docs/pesquisa-web-2026-10.md) | What changed in Codex, Claude Code and others, with sources (in Portuguese) |
| [Research: `/goal`, context and queue](docs/pesquisa-goal-contexto-fila-2026-10.md) | Context rot, cache between cycles, queue mode (Symphony/Linear) (in Portuguese) |
| [`docs/origem/`](docs/origem/) | Source material behind the project |

Status: F0–F5 done; F6 ready (not applied); F7 has the retrospective curve, prospective experiment pending. Details in §8 of the plan.

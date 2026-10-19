# Long Runs

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Long Runs](guia/assets/banner-en.jpg)](https://inematds.github.io/execucao-longa/guia/en/)

A kit to keep an agent (Codex `/goal` or Claude Code `/goal`) working for hours **without losing its way**: a goal with proof of done, state in files and stop rules.

📖 Visual guide: **https://inematds.github.io/execucao-longa/guia/en/**

## In 5 steps

**1. Create the run folder in your project**
```bash
~/projetos/execucao-longa/tools/novo-longrun.sh ~/projetos/my-project my-goal
# → my-project/longrun/2026-10-01-my-goal/ with goal, plan, state, progress, failures, decisions and canal (notes on what compaction loses)
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
3. Install the `session-handoff` and `prime` skills from **[skillmanager3x](https://inematds.github.io/skillmanager3x/guia/en/)** ([repo](https://github.com/inematds/skillmanager3x); same version as the [agente-claude-codex](https://github.com/inematds/agente-claude-codex) kit 1.5.2): `cp -r skill/en/session-handoff skill/en/prime ~/.claude/skills/`. The hook only **asks** for the handoff; those skills write it (`handoff-grava.py`, `latest.md` as an index of open work) and resume it (`/prime`). Since 1.5.2 the handoff checks itself: the script records the commit and sha256 of the files (`handoff-grava.py --conferir` flags a stale handoff), every `[confirmed]` points to a commit, test or file, and 5 test questions let `/prime` show how much it recovered (N/5).
4. In `~/.claude/settings.json`, hook `tools/hook-longrun.sh` to `PreCompact`, `SessionStart` (matcher `compact|resume|clear`), `PostToolUse`, `UserPromptSubmit` and `Stop`. It warns the agent by **context band**, measured against the **point where Claude Code compacts** (~967k on 1M models, per the Claude Code docs; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` or `LONGRUN_TETO` change it. The 200k–575k compactions seen in the logs were **idle** compactions, ~55 min without activity, not size-based): ~50% → note things in `canal.md`; ~70% → update state and `/compact`; ~85% → `/session-handoff` + fresh session + `/prime`. It also says to reread state after compacting or resuming. In any session it asks for a handoff at ~70%/~85% and after compacting, **checks** the transcript for a new file in `handoffs/history/` (re-asks up to 2 times, then reports "handoff verified" or "NOT saved"), asks for a fresh session on the 3rd compaction, and after 60+ min idle with 150k+ context **blocks the next message once** to warn that the cache expired (resend to continue; `/clear` starts clean and the new session points to the last handoff). And set `"cleanupPeriodDays": 365` (the 30-day default deletes transcripts). **Idle handoff (1.5.1, `Stop` event):** at the end of each reply, with context ≥ 200k tokens and a `handoffs/` folder, the hook only **schedules** (a `systemd-run --user` timer, one per session, reset on every reply) a check 45 min later (since 1.9.6; it was 30, and idle compaction comes at about 54 min). If the session is still idle, has no recent handoff and the 1 h cache is still valid (< 55 min), it writes the handoff in a **fork** of the session (`claude -p --resume --fork-session`, same model, warm cache) that may only run `handoff-grava.py` and read files; log in `~/.local/state/execucao-longa/ocioso.log`, and the expired-cache notice mentions the saved handoff. Nobody is interrupted while working anymore: the 1.1–1.4 "Continuous handoff" request (every 30 min of work) is off (`LONGRUN_CONTINUO_TOKENS=200000` turns it back on). **Since 1.8.6** the away summary Claude Code writes when you switch focus (`away_summary`) and local commands such as `/exit` no longer count as "the session moved", and only a handoff written up to 5 min before the last reply counts as recent (before, a 30-min-old handoff left the end of the work out). Knobs: `LONGRUN_OCIOSO_MIN`, `LONGRUN_OCIOSO_TOKENS` (0 turns it off), `LONGRUN_CACHE_MIN`. **Resume measurement (1.6.1):** if the project's newest handoff has the "Perguntas-teste" (test questions) section (agente-claude-codex kit 1.5.2+), after compaction, after `--resume` and on the resend after an expired-cache pause, the hook asks the agent for the 5 answers **from memory, before opening the handoff**; it compares and records the score with `tools/nota-retomada.py`. On a cleared session it asks for the `/prime` score. `python3 tools/nota-retomada.py --relatorio` shows accuracy and context per mode (compactada, retomada, continuada, prime); `LONGRUN_MEDIR=0` turns it off. **Open-work index (1.2.0):** when `latest.md` is an index (written by the session-handoff skill's `handoff-grava.py`, agente-claude-codex kit 1.4.1), a cleared session lists every open piece of work in the project, not just the last one, and flags snapshots whose name stamp is later than the write time (made-up stamp).
5. Watchdog: copy `tools/systemd/longrun-vigia.*` to `~/.config/systemd/user/` and run `systemctl --user enable --now longrun-vigia.timer` (alerts on stopped or idle runs).
6. Cron jobs that call agents: `flock -n <lock> timeout <cap> <script>`.

## "Sessão parada há Xh: o cache venceu" (session idle, cache expired) is not an error

When you return to a session idle for more than 60 min with more than 150k tokens of context, the hook (`UserPromptSubmit`, function `pausa` in `tools/hook-longrun.py`) **holds the first message once**. The prompt cache lasts ~1 h; after that, the next message rereads the whole conversation uncached and burns a lot of your limit. The warning lets you choose before paying.

Real example (session idle for 5h33 with 220k tokens; the hook message is in Portuguese):

```
● UserPromptSubmit operation blocked by hook:
  Sessão parada há 5h33: o cache venceu e esta mensagem vai reprocessar ~220 mil tokens do seu limite.
  Para continuar aqui, reenvie a mensagem. Para começar limpo: /clear e depois /prime
  (o último handoff do projeto é indicado na abertura).

  Original prompt: ficou muito ruim, a movimentação da apresentação...
```

What to do:

- **Keep going in this session:** resend the same message. It goes through (the hold applies once per pause and is saved in the session state).
- **Start light (recommended):** `/clear` then `/prime`. The new session reads the latest handoff and you repeat the request with ~20k tokens instead of 220k.

Each session counts separately: two idle sessions show the warning once each. Tune it with environment variables:

| Variable | Default | Effect |
|---|---|---|
| `LONGRUN_PAUSA_MIN` | `60` | idle minutes before holding (e.g. `120`) |
| `LONGRUN_PAUSA_TOKENS` | `150000` | minimum context to hold; `0` turns it off |

## Cache, automatic handoff and compaction: how it works

**What returning to an idle session costs.** Every message resends the whole conversation. With a warm cache (up to ~1 h since the last reply), that re-read costs ~10% of the normal input price. After 1 h the cache expires: the next message reprocesses everything and writes the cache again (~2× the normal price, about 20× a warm-cache message). In a session at 48% of the context, that is ~480K tokens re-read at once. On a subscription this is not money, but it comes out of your usage quota (5-hour and weekly limits). You pay it once: the following messages are cheap again.

**That is why the handoff has a right time.** Written with a warm cache, a handoff costs one cheap message. Requested after the cache expired, it pays the full re-read itself. `/compact` costs the same, since it also reads everything. If the work is already in files (commits, pending list, CLAUDE.md), you can `/clear` + `/prime` without a handoff, and it is cheap because prime reads only what it needs. Paying the re-read is only worth it when there are decisions that live only in the conversation.

**Automatic handoff on idle.** The agent only runs when a message arrives, and hooks fire on events, not on a clock: without help, nothing writes the handoff while you are doing something else. `tools/hook-longrun.py` handles this on the `Stop` event:

1. At the end of each reply, with context ≥ 200K tokens (~20% of the 1M window) and a `handoffs/` folder in the project, it schedules a timer (`systemd-run --user`, one per session, reset on every reply) for 45 min later.
2. When the timer fires, the hook checks three things: the session is still idle, there is no handoff from this session written up to 5 min before the last reply, and the cache is still valid (< 55 min).
3. If all three hold, it writes the handoff in a **copy** of the session (`claude -p --resume --fork-session`, same model, on the subscription). The copy reads from the warm cache and may only run `handoff-grava.py` and read files. The open session is not touched.
4. Every check is logged in `~/.local/state/execucao-longa/ocioso.log` (written, or why not).

**Timeline of an idle session:**

| Idle time | What happens |
|---|---|
| 0 | the reply ends and the 45-min timer is scheduled |
| 3–12 min | if you switched focus, Claude Code writes an "away summary" (`away_summary`) into the conversation; it does **not** count as activity |
| 45 min | handoff written in the copy, with a warm cache |
| ~54 min | Claude Code compacts on its own for idleness (only above ~200K tokens), still with a warm cache |
| 60 min | the cache expires |
| when you return | if it compacted: the conversation continues from the summary, cheaply, and the hook asks to re-read the handoff with it. If it did not compact and more than 60 min passed: the hook holds the first message once (previous section) and shows `/clear` + `/prime <this session's handoff>` |

**Why 45 min and not 50.** Idle compaction comes between 53 and 58 min, and the copy takes 30–60 s plus Claude's startup. At 50 min it could land after the summary or past the 55-min cache limit. The cost is the same at any time before 1 h (one warm-cache read); 45 leaves margin.

**Automatic compaction does not replace the handoff.** The summary loses detail (decisions, files, what not to do), and it does not always happen. On 2026-10-18 an idle session at 480K tokens was not compacted, and returning paid the full re-read. The 45-min handoff is the safeguard; compaction is a bonus when it comes.

**What made the automatic handoff fail** (fixed in 1.8.5 and 1.8.6):

- **File date.** Claude Code appends untimestamped lines after the reply, and the hook read that as "the session moved". It now decides by the last timestamped line.
- **Switching focus and `/exit`.** `away_summary` and local commands are timestamped and also looked like activity: 7 sessions on 10/16 got no handoff. Now only user messages and agent replies count.
- **An old handoff counting as recent.** A 07:38 handoff covered an 08:06 reply, and the last half hour was lost. Now only a handoff written up to 5 min before the last reply counts. If the cache expires with an automatic handoff older than the last work, the warning says so instead of "no handoff".

| Variable | Default | Effect |
|---|---|---|
| `LONGRUN_OCIOSO_MIN` | `45` | idle minutes before writing (do not go past ~45) |
| `LONGRUN_OCIOSO_TOKENS` | `200000` | minimum context to write; `0` turns it off |
| `LONGRUN_CACHE_MIN` | `55` | after this the copy does not run (the cache would be cold) |

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
| [`tools/hook-longrun.sh`](tools/hook-longrun.sh) | Claude Code hook: context bands (50/70/85% of the compaction point), verified handoff, expired-cache warning, save before compacting, reread afterwards |
| [`tools/vigia.py`](tools/vigia.py) | Watchdog (timer every 10 min): flags runs that stopped, stopped silently or went idle |
| [`tools/arquivar-sessoes.py`](tools/arquivar-sessoes.py) | Hygiene: report on space used by old sessions; `--aplicar` compresses, `--restaurar` restores |
| [`tools/recall.py`](tools/recall.py) | `recall` command: searches everything said with Codex and Claude (SQLite FTS5 index, reindexed hourly) |
| [`tools/faxina-claude-mem.py`](tools/faxina-claude-mem.py) | claude-mem cleanup with backup: old queue, stuck sessions, logs |
| [`templates/`](templates/) | `goal.md` (with the criteria scale), `state/plan/progress/failures/decisions.md`, `/goal` prompts and the LONG-RUN snippet for `AGENTS.md`/`CLAUDE.md` |
| [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/) | Real example: the pilot that built `medir-sessao.py` in 1 cycle |
| [Plan](docs/PLANO-EXECUCAO-LONGA.md) | The full method: criteria (§3.1), state files, recipes, queue mode, guardrails, phases and pilot lessons (in Portuguese) |
| [F7 retrospective](docs/experimento-f7-retrospectivo-2026-10.md) | Cache and cost-per-turn curve on 3 real sessions + experiment protocol (in Portuguese) |
| [Research Jul–Oct 2026](docs/pesquisa-web-2026-10.md) | What changed in Codex, Claude Code and others, with sources (in Portuguese) |
| [Research: `/goal`, context and queue](docs/pesquisa-goal-contexto-fila-2026-10.md) | Context rot, cache between cycles, queue mode (Symphony/Linear) (in Portuguese) |
| [Research: memory, claude-mem and database](docs/pesquisa-memoria-claude-mem-2026-10.md) | Does claude-mem work? Is it useful for the projects? Suggested SQLite FTS5 index (recall) — proposed F8/F9 (in Portuguese) |
| [`docs/origem/`](docs/origem/) | Source material behind the project |

Status: F0–F5 done; F6 ready (not applied); F7 has the retrospective curve, prospective experiment pending. F8 (recall) and F9 (claude-mem cleanup) done. Details in §8 of the plan.

# Execução Longa

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Execução Longa](guia/assets/banner.jpg)](https://inematds.github.io/execucao-longa/guia/)

Kit para deixar um agente (Codex `/goal` ou Claude Code `/goal`) trabalhando por horas **sem perder o rumo**: objetivo com prova de pronto, estado em arquivos e regras de parada.

📖 Guia visual: **https://inematds.github.io/execucao-longa/guia/**

## Em 5 passos

**1. Crie a pasta da execução no seu projeto**
```bash
~/projetos/execucao-longa/tools/novo-longrun.sh ~/projetos/meu-projeto meu-objetivo
# → meu-projeto/longrun/2026-10-01-meu-objetivo/ com goal, plan, state, progress, failures, decisions e canal (notas do que a compactação perde)
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

**5. Feche e meça** — `state.md` diz "concluído", você roda o teste final por conta própria, e:
```bash
python3 ~/projetos/execucao-longa/tools/medir-sessao.py <sessão.jsonl>             # duração, compactações, tokens, cache
python3 ~/projetos/execucao-longa/tools/medir-sessao.py <sessão.jsonl> --json --por-turno
```

**Prefere que rode sozinho?** No lugar do passo 3, ponha `prompt.md` + `loop.env` na pasta (copie de [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/)) e rode `tools/loop-longrun.sh <pasta>`. Cada ciclo é um `codex exec` com teto; quem decide continuar é o teste, e o loop para sozinho (concluído, estagnação ou teto).

## Instalar uma vez por máquina

1. Clone em `~/projetos/execucao-longa`.
2. Cole [`templates/AGENTS-long-run.md`](templates/AGENTS-long-run.md) no `CLAUDE.md` e no `AGENTS.md` globais — o agente passa a seguir o método sem ser lembrado.
3. No `~/.claude/settings.json`, ligue `tools/hook-longrun.sh` em `PreCompact`, `SessionStart` (matcher `compact|resume`), `PostToolUse` e `UserPromptSubmit`. Ele avisa o agente por **faixa de contexto**: ~50% → anotar no `canal.md`; ~70% → atualizar o estado e `/compact`; ~85% → `/session-handoff` + sessão nova + `/prime`. Também manda reler o estado depois de compactar ou retomar. **Em qualquer sessão** (mesmo sem execução longa), em ~70% e ~85% e depois de uma compactação, pede ao agente que grave o handoff sozinho (skill `session-handoff`), enquanto o cache ainda está quente. E ponha `"cleanupPeriodDays": 365` (o padrão de 30 dias apaga as transcrições).
4. Vigia: copie `tools/systemd/longrun-vigia.*` para `~/.config/systemd/user/` e rode `systemctl --user enable --now longrun-vigia.timer` (alerta execução parada ou ociosa).
5. Crons que chamam agente: `flock -n <lock> timeout <teto> <script>`.

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
| [`tools/loop-longrun.sh`](tools/loop-longrun.sh) | Laço headless: ciclos de `codex exec` com flock, timeout e teto de memória; o teste decide; para por estagnação |
| [`tools/medir-sessao.py`](tools/medir-sessao.py) | Mede uma sessão (Codex ou Claude): duração, compactações, tokens, cache, saída de ferramenta, curva por turno |
| [`tools/hook-longrun.sh`](tools/hook-longrun.sh) | Hook do Claude Code: faixas de contexto (50/70/85%) com ação proposta, salvar antes de compactar e reler depois |
| [`tools/vigia.py`](tools/vigia.py) | Vigia (timer a cada 10 min): avisa execução parada, parada sem aviso ou ociosa |
| [`tools/arquivar-sessoes.py`](tools/arquivar-sessoes.py) | Higiene: relatório do espaço das sessões antigas; `--aplicar` comprime, `--restaurar` devolve |
| [`tools/recall.py`](tools/recall.py) | Comando `recall`: busca em tudo o que foi dito com o Codex e o Claude (índice SQLite FTS5, reindexado de hora em hora) |
| [`tools/faxina-claude-mem.py`](tools/faxina-claude-mem.py) | Faxina do claude-mem com backup: fila antiga, sessões presas, logs |
| [`templates/`](templates/) | `goal.md` (com escala de critérios), `state/plan/progress/failures/decisions.md`, prompts `/goal` e o trecho LONG-RUN para `AGENTS.md`/`CLAUDE.md` |
| [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/) | Exemplo real: o piloto que construiu o `medir-sessao.py` em 1 ciclo |
| [Plano](docs/PLANO-EXECUCAO-LONGA.md) | O método completo: critérios (§3.1), arquivos de estado, receitas, modo fila, guardrails, fases e lições do piloto |
| [F7 retrospectiva](docs/experimento-f7-retrospectivo-2026-10.md) | Curva de cache e custo por turno em 3 sessões reais + protocolo do experimento |
| [Pesquisa jul–out/2026](docs/pesquisa-web-2026-10.md) | O que mudou no Codex, Claude Code e outros, com fontes |
| [Pesquisa `/goal`, contexto e fila](docs/pesquisa-goal-contexto-fila-2026-10.md) | Deterioração de contexto, cache entre ciclos, modo fila (Symphony/Linear) |
| [Pesquisa memória: claude-mem e banco](docs/pesquisa-memoria-claude-mem-2026-10.md) | O claude-mem funciona? Serve para os projetos? Sugestão de índice SQLite FTS5 (recall) — proposta F8/F9 |
| [`docs/origem/`](docs/origem/) | Material que originou o projeto |

Status: F0–F5 feitas; F6 pronta (não aplicada); F7 com curva retrospectiva, experimento prospectivo pendente. F8 (recall) e F9 (faxina do claude-mem) feitas. Detalhes no §8 do plano.

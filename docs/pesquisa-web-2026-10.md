# Execução longa de agentes de código: o que mudou entre jul e out/2026

Pesquisa web feita em 01/10/2026, sem APIs pagas. Fontes: páginas públicas, docs oficiais e changelogs. As datas de versão do Claude Code vêm da página pública do pacote no registro npm.

**Legenda de confiabilidade**
- **[OFICIAL]**: doc, changelog ou blog do próprio fornecedor.
- **[COMUNIDADE]**: blog de terceiro, issue do GitHub ou imprensa.
- **[NÃO ENCONTRADO]**: sem fonte localizada.

---

## 0. Checagem do infográfico ("Codex — execução longa")

| Afirmação do infográfico | Situação |
|---|---|
| `/goal` inicia execução longa | **Confirmado [OFICIAL].** No Codex CLI, `/goal` serve para "Set, edit, pause, resume, view, or clear a task goal". A página "Long-running work" manda usar `/goal` no app desktop, no CLI e na extensão de IDE. Segundo relato da comunidade, o comando chegou no CLI 0.128.0, em 30/04/2026. Portanto ele **não é novidade do período jul–out**; o que mudou nesse intervalo foram melhorias (ver tabela). |
| `/compact` força compactação | **Confirmado [OFICIAL].** Descrição oficial: "Summarize the visible chat to free tokens". A compactação automática existe desde set/2025 (CLI 0.36). |
| `/resume` retoma sessão | **Confirmado [OFICIAL]**, junto com `codex resume` na linha de comando. |
| `/fork` ramifica sessão | **Confirmado [OFICIAL].** No CLI, `/fork` "Fork the current chat into a new chat". No app, copia o chat para um chat novo ou para uma worktree. |
| Sessão de 11 dias, 573 turnos, JSONL de 1,3 GB | **[NÃO ENCONTRADO]** como caso específico. Existem relatos parecidos [COMUNIDADE]: issues do Codex mostram logs de sessão entre 700 MB e 2 GB por causa de compactações repetidas (#24948, aberta em 28/05/2026) e um `~/.codex` de 42 GB, porque cada compactação regrava o `replacement_history` inteiro no JSONL (#41806). O número de 1,3 GB é plausível, mas não tem fonte. |
| Arquivos `goal.md plan.md state.md progress.md failures.md decisions.md` | **Não é um padrão oficial com esses nomes.** O padrão oficial da OpenAI é um único `PLANS.md` (ExecPlan), com seções obrigatórias *Progress*, *Surprises & Discoveries*, *Decision Log* e *Outcomes & Retrospective*. Do lado da Anthropic, o padrão usa `claude-progress.txt`/`PROGRESS.md`, `feature_list.json`, `init.sh` e o git. A divisão em seis arquivos é uma adaptação da comunidade das mesmas ideias. |

---

## 1. OpenAI Codex (CLI, app e cloud)

**Goal mode** [OFICIAL]
- A doc "Long-running work" orienta a dar um resultado esperado, restrições e uma definição de pronto. O texto do `/goal` vira ao mesmo tempo o primeiro prompt e o critério de conclusão.
- Se o objetivo ainda estiver vago, a recomendação é começar com `/plan`.
- A tabela oficial pede três elementos: **Outcome**, **Constraints** e **Verification** (testes, medições ou critérios que provem a conclusão).
- No app há uma linha de progresso com pausar, retomar, editar e limpar. Também há o `/side`, para pedir status sem interromper o trabalho.

**Persistência e orçamento** [COMUNIDADE: Daniel Vaughan, 07/05/2026]
- O goal fica guardado como objeto no estado do app-server e sobrevive a compactação, crash e reboot.
- Existe orçamento de tokens com parada suave: quando o orçamento chega perto, o agente encerra de forma organizada. Esse orçamento não é um teto de cobrança.
- Na época era preciso ligar `[features] goals = true` no `config.toml`. As docs atuais não citam essa flag, então ela pode já ter caído.

**Novidades de jul–out/2026** [OFICIAL, changelog]
- **20/07**: goals passam a ser retomados depois de bloqueio ou de atingir o limite de uso.
- **27/07**: progresso mais claro ao pausar ou retomar.
- **07/08**: corrigidos os follow-ups de `/goal` depois que um goal termina.
- **01/09**: tarefas longas mostram o tempo de trabalho ao vivo.
- **17/09**: o daemon do app-server passa a ter agenda de atualização. Threads salvas e goals ativos se recuperam depois de reinício do daemon. Prompts aceitos ficam salvos mesmo se a compactação falhar.
- **25/09** (0.157): atalho `f` para fazer fork de conversa.
- **28/09**: a compactação local preserva as partes de texto do usuário.
- **29/09** (0.159): `instant_interrupt` opcional, para redirecionar o Codex no meio de chamadas longas.

**Modelos** [OFICIAL]
- GPT-6 Astra saiu em **03/09/2026**. Junto veio um mecanismo novo de contexto: em vez de resumir tudo num bloco só, o Codex mantém **notas entre janelas de contexto**, e as janelas anteriores continuam pesquisáveis.
- Segundo a imprensa, esse modo é experimental, liga no `config.toml` e deve virar padrão no Astra [COMUNIDADE: InfoQ e Vaughan].
- GPT-6 Sol e GPT-6 Luna chegaram ao Codex em **22/09**.
- GPT-6.1 Sol virou o modelo padrão do catálogo em **29/09**.
- Relato da comunidade: uma tarefa de 30 min no GPT-5.5 pode virar uma execução de 12 a 24 h no Astra, ou rodar até acabar a cota.

**Relato de sessão longa** [OFICIAL, blog OpenAI Developers]
- GPT-5.3-Codex em "Extra High" rodou **cerca de 25 h sem interrupção**, gastou cerca de 13M de tokens e gerou cerca de 30 mil linhas, para construir uma ferramenta de design do zero.

**Outros** [OFICIAL]
- O `/init` gera o `AGENTS.md`.
- Em jul/2026, projetos com várias pastas passaram a descobrir `AGENTS.md`, skills e `config.toml` na pasta principal.
- Tarefas agendadas podem disparar por eventos do Gmail, Slack e GitHub (25/08).
- **Limite de duração de tarefa no cloud:** [NÃO ENCONTRADO] nenhum número atual. O único limite documentado é antigo: setup script de até 20 min (jun/2025).

---

## 2. Claude Code / Anthropic

**`/goal`** [OFICIAL, CHANGELOG 2.1.139, de 11/05/2026, anterior ao período]
- Você define uma condição de conclusão. Depois de cada turno, um modelo pequeno e rápido (Haiku por padrão) avalia a condição e responde *not yet met*, *met* ou *impossible*.
- Por baixo, é um Stop hook baseado em prompt, restrito à sessão.
- O avaliador não chama ferramentas: julga apenas o que já apareceu na conversa.
- Se houver vários turnos seguidos sem progresso, o loop para.
- Com trabalho rodando em segundo plano, a avaliação espera. Há check-ins a cada 30 min, depois 1 h e depois a cada 2 h; o intervalo é configurável.
- Novidades do período:
  - Check-ins a partir da 2.1.234 (ago/2026).
  - Correção da perda do `/goal` ativo ao retomar uma sessão já compactada (2.1.274, 16/09).

**`/loop`, ScheduleWakeup e tarefas agendadas** [OFICIAL]
- `/loop 5m …` vira um cron. Sem intervalo, o próprio Claude escolhe a espera, entre 1 min e 1 h. No modo dinâmico, o agendamento acontece pelo ScheduleWakeup, que dispara uma vez e precisa ser reagendado a cada rodada [COMUNIDADE: ClaudeWorld].
- Tarefas recorrentes **expiram em 7 dias**.
- Novidades do período:
  - Detalhamento de Loops no `/usage`, para achar loop descontrolado (2.1.243, 24/08).
  - Correção de wakeups disparando a cada segundo (2.1.281, 23/09).

**Routines (cloud, research preview)** [OFICIAL]
- `/schedule` ou `/routines`, com gatilhos por agenda, API e GitHub.
- Limites: 100 execuções agendadas por hora por conta e 30 "run now"/API por hora por routine.
- Gatilho de GitHub pelo CLI desde a 2.1.225.

**Background agents, agent view e workflows** [OFICIAL]
- Antes do período: agent view com `claude agents` (2.1.139), `/resume` para sessões em background (2.1.144, 18/05) e *dynamic workflows*, que orquestram de dezenas a centenas de agentes (2.1.154, 28/05).
- Novidades do período:
  - 01/07: notificações `agent_needs_input` e `agent_completed`.
  - 06/07: tamanho de workflow configurável.
  - 18/07: heartbeat de progresso em tool calls longas.
  - 21/07: teto de 20 subagentes simultâneos.
  - 14/08: limite de memória por cgroup para o Bash.
  - 28/08: comandos `attach/logs/stop/respawn`.
  - 11/09: até 256 agentes simultâneos por workflow.
  - 15/09: fork de sessão do Remote Control como sessão em background.

**Modelos com contexto de 1M** [OFICIAL]

| Data | Modelo | Contexto | Preço (entrada/saída por MTok) | Leitura de cache |
|---|---|---|---|---|
| 24/07 | Opus 5 | 1M | — | — |
| 01/09 | Fable 5.1 | 1M | US$10 / US$50 | US$0,25/MTok |
| 22/09 | Opus 5.5 | 1M | US$4 / US$20 | US$0,20/MTok (era US$0,50) |
| 28/09 | Sonnet 5.5 | 1M | US$2 / US$10 | US$0,20/MTok |

- Sobre o Opus 5.5, o anúncio oficial cita: auditoria de 200 mil linhas em menos de 3 h (o Opus 5 levou mais de 20 h) e port do HAProxy de C para Rust em 9,5 h.
- O número "**18 h** sem supervisão" vem de **depoimento de cliente** no próprio post, não de métrica da Anthropic.

**API: compactação, context editing e memory tool** [OFICIAL]
- Existe compactação do lado do servidor.
- O context editing (`clear_tool_uses_20250919`, beta `context-management-2025-06-27`) apaga resultados antigos de ferramentas.
- Combinado com o memory tool, o Claude recebe um aviso antes da limpeza para salvar o que importa em arquivos de memória.
- Ressalva da doc: com ferramentas do lado do servidor, o SDK pode somar `cache_read_input_tokens` e compactar antes da hora.

**Managed Agents** [OFICIAL]
- Lançado em 08/04/2026 (fora do período): sessões longas hospedadas que sobrevivem a desconexões.
- Custo: preço normal de tokens mais US$0,08 por hora de sessão [COMUNIDADE, na parte de preço].

**Recomendações oficiais de "long-running"** [OFICIAL]
- *Effective harnesses for long-running agents* (26/11/2025):
  - Um agente inicializador cria `init.sh`, `claude-progress.txt`, `feature_list.json` e o repositório git.
  - O agente de código faz uma feature por sessão. Ao começar, roda `pwd`, lê o progresso e o git log e roda um teste ponta a ponta antes de mexer em algo.
  - Deve terminar cada sessão em "clean state".
  - Falhas observadas: tentar fazer tudo de uma vez e declarar a tarefa pronta antes da hora.
- *Harness design for long-running application development* (24/03/2026):
  - Arquitetura planner/generator/evaluator com sprint contracts.
  - A "context anxiety" do Sonnet 4.5 exigia context resets. O Opus 4.5 praticamente eliminou isso, e o harness passou a usar uma sessão contínua com a compactação automática do Agent SDK.
- Repositório oficial `anthropics/cwc-long-running-agents`:
  - `PROGRESS.md` mantido pelo próprio agente.
  - `commit-on-stop.sh`.
  - `/goal` como checador de conclusão.
  - "Re-simplify on model upgrades", ou seja, reavaliar o harness a cada modelo novo.
- **Nenhum post novo de engenharia sobre long-running entre jul e out/2026** apareceu na página Engineering. O mais recente com data é de 23/04/2026.

---

## 3. Outros agentes (só o relevante para execução longa)

- **Cursor** [OFICIAL]:
  - Long-running agents em research preview desde 12/02/2026.
  - Em **19/08/2026**, os cloud agents passaram a reagir a eventos, a "hold a goal until it's met" e a receber direcionamento sem interrupção (o follow-up espera a próxima tool call).
  - Ajustes no harness com cortes de token e mais reaproveitamento de cache [COMUNIDADE: Releasebot, set/2026].
- **Google** [OFICIAL]:
  - O Gemini CLI está sendo substituído pelo **Antigravity CLI** (anúncio de 19/05/2026). O plano de consumidor parou em 18/06/2026.
  - O Jules segue como agente assíncrono em VM [COMUNIDADE].
  - Nenhuma novidade específica de execução longa no período [NÃO ENCONTRADO].
- **Devin** [OFICIAL, release notes]:
  - 26/08: status "Waiting" e mensagens na fila entregues durante esperas longas.
  - Automations com sessão longa que recebe os eventos seguintes.
  - Modelo SWE-1.7 treinado com self-compaction e tarefas de até 6 h [COMUNIDADE].
- **Factory** [COMUNIDADE]:
  - Rodada de US$200M em 15/09.
  - Relato de sessões de Droid vivas por semanas (Chainguard).
  - "Droid Computers" persistentes.
- **Amp** [COMUNIDADE]: app desktop em 04/09. Nada específico sobre execução longa.

---

## 4. Métricas, cache e compactação

**METR time horizon** [OFICIAL]
- Em 29/01/2026 saiu o TH1.1, com 228 tarefas, das quais 31 longas (8 h ou mais).
- A última atualização da página é de **08/05/2026**: Claude Mythos Preview, com horizonte de 50% de pelo menos 16 h. O próprio METR avisa que "medições acima de 16 h não são confiáveis" com a suíte atual.
- **Nenhuma medição METR publicada entre jul e out/2026** para Opus 5, Opus 5.5, Fable 5.1 ou GPT-6 [NÃO ENCONTRADO]. A tendência citada é crescimento de cerca de 10x por ano, com dobra a cada ~4,3 meses [COMUNIDADE: LessWrong].

**Prompt caching na OpenAI** [OFICIAL] (GPT-5.6 em diante)
- Escrita de cache custa 1,25x a entrada normal.
- Leitura custa 0,1x, ou 0,05x no GPT-6.1 Sol.
- TTL de `"30m"` via `prompt_cache_options.ttl`, com breakpoints explícitos.
- Prefixo mínimo de 1.024 tokens.
- Para mudar o esforço de raciocínio sem quebrar o prefixo no GPT-6, usar `configuration_update`.

**Prompt caching na Anthropic** [OFICIAL]
- Escrita com TTL de 5 min custa 1,25x a entrada normal; com TTL de 1 h, 2x.
- Leitura (hit): US$0,20/MTok no Opus 5.5 e no Sonnet 5.5, e US$0,25/MTok no Fable 5.1.

**Compactação × cache** [OFICIAL, OpenAI]
- A compactação troca o histórico por uma versão mais curta e muda o prefixo, então o primeiro request depois dela aproveita menos cache.
- Orientação da doc: manter instruções estáveis no início e comparar o custo total. Menos tokens podem compensar a queda na taxa de acerto do cache.
- Na prática, cada compactação = uma nova escrita de cache. Em sessões de dias, a leitura de cache barata (US$0,20 por MTok) passa a ser o maior item da conta, e foi justamente esse preço que a Anthropic cortou no Opus 5.5.

---

## 5. Boas práticas consolidadas

1. **Estado fora do contexto.** Use um arquivo vivo (`PLANS.md`/`PROGRESS.md`) com progresso, decisões, surpresas e próximos passos, e releia esse arquivo no começo de cada sessão ou depois de cada compactação. (OpenAI ExecPlans; Anthropic harness)
2. **Critério de parada verificável.** O goal precisa conter Outcome, Constraints e Verification. Na Anthropic, a condição é julgada por um avaliador separado. Evite "até ficar bom".
3. **Testes como oráculo.** Rode um teste ponta a ponta *antes* de começar algo novo, para pegar o estado quebrado da sessão anterior, e marque features como "passa" só depois de testadas.
4. **Git como memória e checkpoint.** Faça commit em marcos, use `git log` como segundo registro e um commit-on-stop como rede de segurança. Use `/fork` ou worktree para testar caminhos alternativos.
5. **Uma unidade de trabalho por sessão.** Isso evita a tentativa de fazer tudo de uma vez e a sessão seguinte herdando trabalho pela metade.
6. **Orçamentos e tetos.** Use orçamento de tokens (parada suave), detecção de turnos sem progresso, expiração de loops (7 dias), teto de subagentes e limite de memória.
7. **Riscos:**
   - **Deriva de objetivo e conclusão prematura**: o agente declara pronto ou entra em "context anxiety".
   - **Context rot**: estudos de 2026 relatam que a degradação acompanha o número de passos mais do que o tamanho do contexto [COMUNIDADE: arXiv 2609.01660].
   - **Perda de detalhe a cada compactação.**
   - **Custo**: cache reescrito, sessões de 12 a 24 h.
   - **Loops descontrolados.**
   - **Logs JSONL de vários GB.**
8. **Reavaliar o harness a cada modelo novo.** Modelos mais recentes desviam menos, e muitas muletas viram peso morto.

---

## Novidades jul–out/2026

| Data | Produto | Novidade | Fonte |
|---|---|---|---|
| 01/07 | Claude Code 2.1.198 | Notificações de background agent (`agent_needs_input/completed`) | CHANGELOG [OFICIAL] |
| 18/07 | Claude Code 2.1.214 | Heartbeat de progresso em tool calls longas | CHANGELOG [OFICIAL] |
| 20/07 | Codex | Goals retomam após bloqueio ou limite de uso | Codex changelog [OFICIAL] |
| 21/07 | Claude Code 2.1.217 | Teto de 20 subagentes simultâneos | CHANGELOG [OFICIAL] |
| 24/07 | Anthropic | Claude Opus 5 (1M de contexto) | CHANGELOG 2.1.219 [OFICIAL] |
| 19/08 | Cursor | Cloud agents seguram o goal até cumprir e reagem a eventos | cursor.com/changelog/08-19-26 [OFICIAL] |
| 24/08 | Claude Code 2.1.243 | Detalhamento de Loops no `/usage` | CHANGELOG [OFICIAL] |
| 25/08 | Codex/ChatGPT | Tarefas agendadas disparadas por Gmail, Slack e GitHub | Codex changelog [OFICIAL] |
| 26/08 | Devin | Status "Waiting" e mensagens na fila em esperas longas | docs.devin.ai [OFICIAL] |
| 01/09 | Anthropic | Claude Fable 5.1 (1M, cache de leitura a US$0,25) | CHANGELOG 2.1.257 [OFICIAL] |
| 01/09 | Codex | Tempo de trabalho ao vivo em tarefas longas | Codex changelog [OFICIAL] |
| 03/09 | OpenAI | GPT-6 Astra, com notas entre janelas de contexto e janelas anteriores pesquisáveis | openai.com/index/gpt-6-astra [OFICIAL] |
| 11/09 | Claude Code 2.1.269 | Até 256 agentes simultâneos por workflow | CHANGELOG [OFICIAL] |
| 16/09 | Claude Code 2.1.274 | `/goal` não se perde ao retomar sessão compactada | CHANGELOG [OFICIAL] |
| 17/09 | Codex CLI | Goals ativos se recuperam após reinício do daemon | Codex changelog [OFICIAL] |
| 22/09 | Anthropic | Opus 5.5 (US$4/US$20, cache de leitura de US$0,50 para US$0,20) | anthropic.com/news/claude-opus-5-5 [OFICIAL] |
| 22/09 | OpenAI | GPT-6 Sol e Luna no Codex | Codex changelog [OFICIAL] |
| 23/09 | Claude Code 2.1.281 | Correção de wakeups de `/loop` disparando a cada segundo | CHANGELOG [OFICIAL] |
| 28/09 | Anthropic | Sonnet 5.5 (1M) | CHANGELOG 2.1.284 [OFICIAL] |
| 29/09 | Codex CLI 0.159 | GPT-6.1 Sol como padrão e `instant_interrupt` | Codex changelog [OFICIAL] |

---

## Fontes

**OpenAI**
- Codex changelog: https://developers.openai.com/codex/changelog (consultado em 01/10/2026)
- Long-running work: https://developers.openai.com/codex/long-running-work (sem data)
- Slash commands do CLI: https://developers.openai.com/codex/cli/slash-commands
- Slash commands do app: https://developers.openai.com/codex/reference/slash-commands
- Using PLANS.md: https://developers.openai.com/cookbook/articles/codex_exec_plans
- Run long horizon tasks with Codex: https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
- Prompt caching: https://developers.openai.com/api/docs/guides/prompt-caching
- Compaction: https://developers.openai.com/api/docs/guides/compaction
- GPT-6 Astra (03/09/2026): https://openai.com/index/gpt-6-astra/
- InfoQ sobre o Astra (set/2026): https://www.infoq.com/news/2026/09/openai-gpt6-astra/

**Comunidade sobre o Codex**
- Vaughan, `/goal` (07/05/2026): https://codex.danielvaughan.com/2026/05/07/codex-cli-goal-command-persisted-long-horizon-workflows-pause-resume-budget/
- Vaughan, Astra (03/09/2026): https://codex.danielvaughan.com/2026/09/03/gpt-6-astra-codex-cli-configuration-context-notes-safety/
- Codex issue #24948 (28/05/2026): https://github.com/openai/codex/issues/24948
- Codex issue #41806: https://github.com/openai/codex/issues/41806

**Anthropic / Claude Code**
- CHANGELOG: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (datas pelo registro npm)
- `/goal`: https://code.claude.com/docs/en/goal
- Tarefas agendadas e `/loop`: https://code.claude.com/docs/en/scheduled-tasks
- Routines: https://code.claude.com/docs/en/routines
- Effective harnesses for long-running agents (26/11/2025): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Harness design for long-running apps (24/03/2026): https://www.anthropic.com/engineering/harness-design-long-running-apps
- Repositório de harness: https://github.com/anthropics/cwc-long-running-agents
- Claude Opus 5.5 (22/09/2026): https://www.anthropic.com/news/claude-opus-5-5
- Opus 5.5 na AWS: https://aws.amazon.com/blogs/machine-learning/claude-opus-5-5-is-now-available-on-aws/
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Context editing: https://platform.claude.com/docs/en/build-with-claude/context-editing
- Compaction: https://platform.claude.com/docs/en/build-with-claude/compaction
- Managed Agents (08/04/2026): https://claude.com/blog/claude-managed-agents
- Comunidade sobre ScheduleWakeup: https://claude-world.com/tutorials/s31-scheduled-autonomy/

**Outros agentes**
- Cursor (19/08/2026): https://cursor.com/changelog/08-19-26
- Cursor long-running agents: https://cursor.com/blog/long-running-agents
- Google, transição para o Antigravity CLI (19/05/2026): https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- Devin release notes 2026: https://docs.devin.ai/release-notes/2026

**Métricas e pesquisa**
- METR time horizons (última atualização em 08/05/2026): https://metr.org/time-horizons/
- METR TH1.1 (29/01/2026): https://metr.org/blog/2026-1-29-time-horizon-1-1/
- LessWrong, "10x/year": https://www.lesswrong.com/posts/EYb2K9acKfyG2bome/metr-time-horizons-now-10x-year
- arXiv 2609.01660, "How Fast Do Agents Rot?": https://arxiv.org/pdf/2609.01660

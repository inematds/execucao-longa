# `/goal`, deterioração de contexto, cache aquecido e modo fila

Pesquisa feita em 01/10/2026, sem APIs pagas. Complementa `pesquisa-web-2026-10.md` (não a substitui). Mesma legenda: **[OFICIAL]**, **[COMUNIDADE]**, **[NÃO ENCONTRADO]**.

Ponto de partida: um relato da comunidade com três ideias — (1) JSONL de 3 GB não é limite, (2) orquestrador acordado por cron a cada ~25 min para não perder o cache, (3) fila de tarefas no Linear com parada quando não houver issue aberta — e a pergunta "o `/goal` sofre deterioração de contexto?".

---

## 1. O `/goal` deteriora o contexto?

**Resposta curta: o `/goal` em si não deteriora nada; quem deteriora é a sessão longa e, principalmente, a compactação repetida.** O `/goal` só torna esse cenário comum, porque mantém o agente trabalhando por horas na mesma conversa.

**O que se observa** [COMUNIDADE, issue openai/codex #34095, aberta em 19/07/2026, rótulos `bug`, `context`, `model-behavior`]
- Depois de muitas compactações automáticas, o objetivo geral sobrevive e o agente ainda cita arquivos e achados específicos. O que se perde é a **fronteira de execução**: o que já está feito, o que falta e qual é o próximo passo exato.
- Sintoma típico: o agente anuncia de novo e de novo "termino os últimos itens, rodo a verificação e faço commit", reabre trabalho já feito, descobre "mais coisas" e **nunca chega ao estado final**. Não é amnésia; é falta de convergência.
- O próprio autor corrigiu o relato original: não ficou provado que a causa seja o esforço "Ultra" nem que só o prompt inicial sobreviva.
- Issue relacionada: #32922, sobre o goal persistido sendo descartado na compactação. Pode ter a mesma origem, não está provado.
- O que a issue pede como comportamento esperado é, na prática, um checkpoint explícito depois de cada compactação: objetivo e restrições; ações concluídas com evidência; itens pendentes; próximo passo exato; condição de término; "não repetir" explícito.

**Por que acontece** [COMUNIDADE]
- *Context rot*: a precisão cai conforme o contexto cresce, mesmo com a informação presente. Estudos de 2026 relatam que a queda acompanha mais o número de passos que o tamanho (ver `pesquisa-web-2026-10.md` §5).
- A compactação automática dispara perto de ~95% da janela, justamente quando o modelo está no pior momento para resumir. Cada compactação perde detalhe e as perdas se acumulam.
- O resumo é feito sem saber o que o agente vai precisar depois, e os passos seguintes já partem do resumo, então o erro se propaga de forma coerente e silenciosa (paper *Slipstream*, arXiv 2605.08580, 09/05/2026, que propõe compactar em paralelo e validar o resumo contra os passos reais).
- No Codex, com modelos hospedados pela OpenAI, a compactação automática roda no servidor e **ignora o `compact_prompt`**; só o `/compact` manual usa o caminho local configurável (Daniel Vaughan, 14/05/2026, Codex CLI v0.130).

**Sinais de que a sessão degradou**
- O agente repete o mesmo plano de fechamento por vários ciclos sem fechar.
- Reabre itens já marcados como feitos ou "redescobre" trabalho.
- Contradiz uma decisão anterior ou esquece uma restrição dada no início.
- Mais de 2–3 compactações na mesma sessão com uso de contexto acima de 80%.
- O Codex ainda não mostra contador de compactações (pedido em #22220; hooks PreCompact/PostCompact pedidos em #16098, não implementados até a data do artigo). Dá para contar pelo JSONL.

**Do lado do Claude Code** [OFICIAL, ver `pesquisa-web-2026-10.md` §2]
- O avaliador do `/goal` é um modelo pequeno que só lê a conversa. Se a conversa foi compactada, ele julga o resumo. Por isso a condição tem que ser algo que o agente **mostra** a cada vez (saída do teste), não algo que "aconteceu lá atrás".
- A 2.1.274 (16/09) corrigiu a perda do `/goal` ativo ao retomar uma sessão compactada — ou seja, o problema existiu.

**O que funciona contra a deterioração**
1. **Estado fora da conversa** (já é o centro do plano): `state.md`/`progress.md` com feito, pendente e próximo passo, relidos depois de toda compactação. É exatamente o checkpoint que a issue #34095 pede ao Codex.
2. **Compactar cedo e manualmente** (~60–80%), com prompt de handoff estruturado, em vez de esperar o automático a 95%. No Codex: `model_auto_compact_token_limit` mais baixo e `/compact` manual.
3. **Contar compactações** e tratar a 3ª como alerta: avaliar handoff + sessão nova.
4. **Detector de não-convergência**: N ciclos sem um item novo fechado com evidência → parar (já é a regra dos 3 ciclos do plano).
5. **Unidades menores**: um goal por feature, em vez de um goal gigante.

---

## 2. Acordar o modelo antes do cache expirar

**Os números do relato conferem com a pesquisa anterior** (`pesquisa-web-2026-10.md` §4) — corrigindo a minha primeira leitura, feita de memória:

| Provedor | Tempo de vida do cache | Leitura | Escrita |
|---|---|---|---|
| OpenAI (GPT-5.6+) | `"30m"` via `prompt_cache_options.ttl` [OFICIAL] | 0,1x (0,05x no GPT-6.1 Sol) | 1,25x |
| Anthropic | 5 min (padrão) ou 1 h | 0,1x | 1,25x (5 min) / 2x (1 h) |

- **"Cache cai em ~30 min"**: bate com o TTL de 30 min da OpenAI. No Claude, o equivalente é 5 min ou 1 h.
- **"Até 20x mais caro"**: perder o cache troca uma leitura de 0,1x por uma escrita de 1,25x–2x → **12,5x a 20x** no Claude; no GPT-6.1 Sol, 1,25x ÷ 0,05x = **25x**. A afirmação procede.
- **"98% de acerto"**: compatível com o > 95% já registrado.

**Quando compensa acordar só para manter o cache**
- Cada acordada lê o contexto inteiro do cache (0,1x ou 0,05x) e, num cache hit, renova o tempo de vida.
- Ponto de equilíbrio aproximado: escrita ÷ leitura. OpenAI: 1,25 ÷ 0,1 ≈ 12 acordadas (≈ 5 h a cada 25 min); GPT-6.1 Sol: ≈ 25 acordadas (≈ 10 h). Claude com TTL de 1 h: 2 ÷ 0,1 = 20 acordadas (≈ 18 h a cada 55 min).
- Conclusão: vale **se houver trabalho previsto dentro dessas horas**; para pausas longas (noite, fim de semana) é melhor deixar expirar ou fazer handoff.
- Pela assinatura, o custo vira **cota**, não dólar — mas a conta é a mesma.
- O Claude Code orienta não agendar ScheduleWakeup só para manter o cache aquecido; o agendamento deve seguir o que se está esperando. A regra útil é a outra: **quando houver espera entre ciclos de trabalho, o intervalo deve ficar abaixo do TTL** (no Claude Code o intervalo do ScheduleWakeup vai de 60 s a 3.600 s).

---

## 3. Modo fila (tracker como painel de controle)

**Existe um padrão oficial parecido** [OFICIAL, via resultado de busca — a página da OpenAI respondeu 403 ao acesso direto]
- **Symphony** (OpenAI, especificação aberta para orquestrar o Codex): transforma um quadro de tarefas como o **Linear** em painel de controle. Cada issue aberta ganha um workspace e um agente; o orquestrador vigia o quadro e garante que toda tarefa ativa tenha agente rodando até terminar; humanos revisam o resultado.
- Há variações da comunidade (ex.: Crewd, "tracker-driven orchestrator") [COMUNIDADE].
- Problemas relatados nesses orquestradores: workspaces que ficam vivos depois do fim, parada que aborta no primeiro erro, filas travadas. Ou seja, **o critério "fila vazia" precisa de um desligamento explícito** [COMUNIDADE].

**Riscos do critério "nenhuma issue aberta"**
- Fechar sem fazer é o caminho mais curto para cumprir o critério. Exigir evidência (saída de teste, arquivo, hash de commit) para fechar.
- Se o agente cria issues, a fila pode não acabar. Teto de issues criadas pelo agente por ciclo/execução, ou portão humano.
- Linear (e GitHub Issues) passam por MCP/API: pela regra do usuário, **exigem autorização explícita**. Começar com fila local em arquivos.

**Por que agrega ao plano**: o plano atual é de objetivo único. A fila cobre o caso de backlog que cresce e trabalho distribuído entre agentes, e cada tarefa vira uma sessão curta — o que, pela seção 1, também reduz a deterioração.

---

## 4. JSONL grande

- O tamanho do arquivo de log não é limite de execução; visualizadores eficientes (o relato cita um em Rust) navegam arquivos de 3 GB.
- O custo real está no contexto e nas compactações, e o tamanho do JSONL vem quase todo de saída de ferramenta regravada a cada compactação (issues #24948 e #41806, ver pesquisa anterior). Tamanho do JSONL = **métrica de diagnóstico**, não teto.

---

## 5. Alerta por faixa de contexto, "canal de sessão" e busca no histórico [COMUNIDADE, relato]

- **Alertas por faixa**: hooks que medem o uso do contexto e injetam no agente um aviso com uma proposta de ação por faixa — o agente passa a "saber" quanto contexto resta. A % pode vir do mesmo cálculo do statusline. Adotado no plano (guardrail 7) com faixas 50/70/85%; no teste real, o aviso chega uma chamada de ferramenta depois, porque a transcrição é gravada com atraso.
- **Canal de sessão**: um arquivo de texto que só cresce, com o que orientaria o orquestrador — aprendizados, fatos, glossário — capturado **cedo**, funcionando como uma "instrução de compactação" do projeto. Adotado como `canal.md` na pasta `longrun/`. É a mesma ideia das notas entre janelas do GPT-6 Astra.
- **Busca em todas as transcrições** ("RECALL"): base local com busca rápida sobre tudo o que foi conversado com qualquer modelo, em qualquer máquina, preservada mesmo quando as sessões são apagadas. Não adotado ainda: sobrepõe-se ao `claude-mem` já instalado (que precisa de checagem). Achado relacionado: o Claude Code apagava as transcrições após 30 dias (`cleanupPeriodDays` padrão); nesta máquina passou para 365.

---

## Fontes

- openai/codex issue #34095 — *Repeated auto-compaction degrades execution frontier and prevents convergence in long tasks*: https://github.com/openai/codex/issues/34095
- Hacker News — *Why codex /goal fails on complex workflows: compaction amnesia and context rot* (não foi possível ler a página; citado só como existente): https://news.ycombinator.com/item?id=48275853
- Daniel Vaughan — *Context Health Monitoring in Codex CLI* (14/05/2026): https://codex.danielvaughan.com/2026/05/14/codex-cli-context-health-monitoring-compaction-telemetry-long-session-quality/
- Daniel Vaughan — *Context Compaction Deep Dive* (14/04/2026): https://codex.danielvaughan.com/2026/04/14/context-compaction-deep-dive-codex-cli-claude-code-opencode/
- Chen et al. — *Slipstream: Trajectory-Grounded Compaction Validation for Long-Horizon Agents*, arXiv 2605.08580: https://arxiv.org/abs/2605.08580
- SitePoint — *Claude Code Context Management Guide*: https://www.sitepoint.com/claude-code-context-management/
- OpenAI — *An open-source spec for Codex orchestration: Symphony*: https://openai.com/index/open-source-codex-orchestration-symphony/
- StGerman/Crewd — *Tracker-driven orchestrator for Code Agents*: https://github.com/StGerman/Crewd
- Augment Code — *9 Open-Source Agent Orchestrators for AI Coding (2026)*: https://www.augmentcode.com/tools/open-source-agent-orchestrators

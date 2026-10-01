# Plano — como usar execuções longas (Codex + Claude Code)

Data: 01/10/2026. Base: material de origem (`docs/origem/`), pesquisa web (`docs/pesquisa-web-2026-10.md`) e pesquisa sobre `/goal`, deterioração de contexto, cache e modo fila (`docs/pesquisa-goal-contexto-fila-2026-10.md`).

---

## 1. A ideia em uma frase

Execução longa **não** é "deixar o agente rodando 10 horas". É dar ao agente **um objetivo com condição de pronto verificável**, **estado em arquivos** (não na memória da conversa) e **tetos** (tempo, tokens, memória). Assim ele trabalha em ciclos até concluir, sobrevive a compactações e retomadas, e qualquer outra sessão consegue continuar do ponto onde parou.

```
OBJETIVO → ESTADO → EXECUTA → TESTA → OBSERVA → CORRIGE → SALVA ESTADO → CONTINUA ↺
```

## 2. O que a pesquisa confirmou (e corrigiu) no material de origem

| Material de origem | O que vale na prática (out/2026) |
|---|---|
| `/goal` no Codex inicia execução longa | **Confirmado.** No Codex CLI ele vive dentro do TUI: `/goal`, `/goal edit\|pause\|resume\|clear`, `/goals` (não aparece no `codex --help`). Chegou em abr/2026; o novo do período é retomada após limite de uso (20/07) e após reinício do daemon (17/09). |
| `/compact`, `/resume`, `/fork` | Confirmados nas docs oficiais. |
| Sessão de 11 dias / 573 turnos / 1,3 GB | **Sem fonte pública.** Plausível: há issues do Codex com logs de sessão de 0,7–2 GB, quase todo o volume é saída de ferramenta regravada a cada compactação. |
| Seis arquivos (`goal/plan/state/progress/failures/decisions.md`) | **Não é padrão oficial.** OpenAI usa um `PLANS.md` (ExecPlan) com seções Progress / Surprises / Decision Log / Outcomes. Anthropic usa `PROGRESS.md` + `feature_list.json` + `init.sh` + git. Os seis arquivos são a mesma ideia, separada. Adotamos os seis (§4) porque cada um tem um leitor diferente. |
| "Mantenha o cache ativo" | O cache funciona sozinho enquanto o prefixo não muda (hit típico > 95% em sessões contínuas). Compactação troca o prefixo e baixa o hit logo depois — é esperado; o que importa é o custo total. |
| (relato da comunidade) "`/goal` funciona, mas deteriora o contexto" | **Procede, com nuance.** O `/goal` não causa a deterioração; a sessão longa com compactações repetidas causa. O objetivo sobrevive, mas se perde o "o que já está feito / o que falta" e o agente não converge (issue openai/codex #34095). Remédio: estado em arquivo relido após cada compactação, compactar cedo, contar compactações (§6.7). |
| (relato da comunidade) Cache cai em ~30 min; perder custa até 20x | **Confere.** OpenAI: TTL de 30 min; Claude: 5 min ou 1 h. Perder o cache custa 12,5x–20x (Claude) e até 25x (GPT-6.1 Sol). Ver §6.8. |
| (não citado) Claude Code também tem `/goal` | **Sim**, desde mai/2026: um modelo pequeno avalia a condição após cada turno (Stop hook). Mais `/loop`, background agents, workflows e routines. |

Novidades que mudam o jogo: **GPT-6 Astra (03/09)** guarda notas entre janelas de contexto em vez de resumir num bloco, e **Claude Opus 5.5 (22/09)** baixou a leitura de cache para US$0,20/MTok com 1M de contexto. Os dois tornam sessões longas mais baratas e menos amnésicas — mas não dispensam o estado em arquivo.

## 3. Quando usar (e quando NÃO)

**Usar execução longa quando** (todos verdadeiros):
- o objetivo é um só e cabe numa frase com **condição de pronto testável** (build passa, N páginas geradas e validadas, auditoria ≥ 9/10, etc.);
- o trabalho é majoritariamente **reversível** e local (código, geração, testes);
- dá para **medir progresso** a cada ciclo (teste, contagem, script de validação).

**Não usar / quebrar em sessões menores quando:**
- o objetivo muda no meio — abrir sessão nova a partir de um handoff, não esticar a antiga;
- há passos **pagos ou irreversíveis** no caminho (render pago, chamadas de API, deploy em produção, envio de e-mail) — esses viram **portão humano**, não passo automático;
- o agente já repetiu 3 ciclos sem progresso mensurável (estagnação → parar e registrar em `failures.md`).

**Regra de bolso:** sessão contínua enquanto o contexto acumulado ainda é útil; quando não for, **handoff + sessão nova** é mais barato e mais limpo que mais uma compactação.

### 3.1 Como classificar um critério de pronto

Bom critério = **alguém de fora consegue checar sem confiar no agente** e **o agente não consegue cumprir por atalho**.

| Nível | Tipo | Exemplo | Problema |
|---|---|---|---|
| **0 — vago** | intenção | "deixar o site bom" | ninguém sabe quando acabou |
| **1 — subjetivo** | julgamento do próprio agente | "código revisado e limpo" | o agente se autoaprova |
| **2 — mensurável, mas burlável** | comando ou contagem | "`npm test` com 0 falhas", "20 páginas geradas" | apaga teste, comenta código, gera página vazia |
| **3 — mensurável e protegido** | comando + trava | "0 falhas **e** ≥ 48 testes **e** `tests/` intocado"; "20 páginas **e** validador aprova cada uma" | **mínimo aceito em execução longa** |
| **4 — verificação independente** | nível 3 + checagem externa | teste ponta a ponta real, avaliador separado, amostra conferida por humano | quando o erro custa caro |

**Cinco perguntas** (cada "não" derruba o nível):
1. Dá para checar com um comando (`<comando> → <saída esperada>`)?
2. A resposta é sim/não, sem "melhorou"?
3. É impossível cumprir sem fazer o trabalho? Se não, falta trava: contagem mínima, arquivo congelado (hash), validador do conteúdo.
4. A prova aparece na saída? O avaliador do `/goal` no Claude só lê a conversa.
5. Cobre **função** (faz o que devia), **regressão** (não quebrou o resto) e **limite** (não mexeu/gastou onde não devia)?

**Sinais de critério ruim:** palavras como "bom", "limpo", "adequado", "completo"; depende de o agente dizer que terminou; só contagem sem checar conteúdo; não diz o que **não** pode mudar; verificação que leva horas (separar teste rápido por ciclo do teste completo no final).

**Exemplo** — "traduzir o guia para inglês": nível 0 é a frase em si; nível 2 é "existe `guia/en/index.html`"; nível 3–4 é "mesmas `<section id>` que o PT (script), nenhum trecho em PT (detecção de idioma), links internos respondem 200, captura de tela conferida".

O `templates/goal.md` já traz as três camadas, a escala e as perguntas.

## 4. Padrão de arquivos de estado (por execução)

Cada execução longa ganha uma pasta própria dentro do projeto:

```
<projeto>/longrun/<AAAA-MM-DD>-<slug>/
  goal.md        objetivo, critérios de pronto (verificáveis), restrições, tetos, portões humanos
  plan.md        estratégia atual + próximos 3 passos (reescrito, não acumulado)
  state.md       o que funciona agora, o que falta, como retomar (comandos exatos)
  progress.md    checkpoints com data/hora + hash do commit (só acrescenta)
  failures.md    erro → tentativa → resultado (só acrescenta)
  decisions.md   decisão → motivo → alternativa descartada (só acrescenta)
  canal.md       conhecimento do projeto que a compactação perde: fatos, aprendizados, glossário, armadilhas (só acrescenta)
```

Os seis primeiros guardam a **tarefa**; o `canal.md` guarda o **contexto** (o que orientaria alguém que chegasse agora). Ele é preenchido cedo — o hook pede isso na faixa de ~50% do contexto — para não depender do resumo da compactação.

- Modelos prontos em `templates/`; prompts de partida em `templates/prompt-goal-*.md`.
- Ao terminar: a menor correção de cada falha vai para o registro de falhas do projeto e o resumo vira um handoff para a próxima sessão.
- **Git é a segunda memória:** commit a cada checkpoint de `progress.md`. Em repo compartilhado, nunca `git add -A`.
- Após **qualquer** compactação ou retomada: reler `goal.md` → `state.md` → `plan.md` → últimas linhas de `progress.md`/`failures.md` antes de agir.

## 5. Receitas por ferramenta

### 5.1 Codex interativo (TUI) — a execução longa "oficial"
1. `cd <projeto>` e criar a pasta `longrun/...` a partir de `templates/`.
2. `codex` (pela assinatura).
3. Colar `templates/prompt-goal-codex.md` preenchido em `/goal ...` — o texto do goal precisa ter **Resultado, Restrições e Verificação**.
4. Acompanhar com `/goals`; pausar/retomar com `/goal pause|resume`; pedir status sem interromper com `/side`.
5. Se o objetivo ainda está vago: `/plan` antes do `/goal`.
6. Usar `/fork` (ou git worktree) para caminhos alternativos sem sujar a linha principal.

### 5.2 Codex headless (`codex exec`) — lotes e scripts
- `codex exec -m <modelo> -s <modo> --skip-git-repo-check - < prompt.md` — stdin **fechado** (sem isso o processo espera entrada e trava).
- Sempre com teto: `timeout 4h`, limite de memória (`systemd-run --user --scope -p MemoryMax=...`) quando gerar carga, `flock` se vier de cron.
- O prompt aponta para os arquivos de estado; cada execução é um ciclo curto; o laço externo decide se roda o próximo ciclo pelo **resultado do teste**, não pelo que o agente diz.
- Pronto: `tools/loop-longrun.sh <pasta-longrun>` + `loop.env` (testes rápido/final, arquivos protegidos e permitidos, teto de ciclos, memória). Faz flock, timeout e `MemoryMax` por ciclo, reverte e conta como falho o ciclo que mexer em teste protegido, faz commit de checkpoint e para por estagnação. Exemplo real: `longrun/2026-10-01-medir-sessao/`.

### 5.3 Claude Code
- **`/goal <condição>`**: o avaliador só vê a conversa, então a condição deve ser algo que o agente **mostra** na saída (ex.: "a saída do `npm test` mostra 0 falhas").
- **Background agents / workflows**: para lotes paralelos de partes independentes; respeitar o teto de agentes simultâneos.
- **`/loop`** (dinâmico, com ScheduleWakeup): para **vigiar** algo externo (fila, render, CI), não para "trabalhar mais". Loops expiram em 7 dias.
- **Routines / `/schedule`** (nuvem): rodam fora da máquina — avaliar antes o que elas acessam.
- `claude -p` em cron: sempre com `timeout`, `flock` e `--max-turns`.

### 5.4 Modo fila — orquestrador + backlog
Em vez de um objetivo único, uma **fila de tarefas** que pode crescer; o orquestrador pega a próxima, despacha (sessão curta, subagente ou `codex exec`), confere e fecha. **Critério de parada: nenhuma tarefa aberta.** É o padrão do Symphony (OpenAI), que usa o Linear como painel de controle.

- **Fila local primeiro**: `longrun/<execução>/tasks/NNN-slug.md`, uma tarefa por arquivo, com `status: aberta|andamento|feita|bloqueada`, critério de pronto e campo `evidencia:`. Linear ou GitHub Issues só depois, com **autorização explícita** de uso do MCP/API.
- **Fechar exige evidência**: saída do teste, arquivo gerado ou hash de commit no campo `evidencia:`. Sem evidência a tarefa volta para `aberta` — senão "fechar sem fazer" vira o atalho para cumprir o critério.
- **Fila com fim**: o agente pode criar no máximo N tarefas por execução (padrão 5); acima disso, a tarefa nova entra como `proposta` e espera aprovação humana.
- **Desligamento explícito**: fila vazia → orquestrador encerra workers, registra o fechamento em `progress.md` e para. Tarefa `bloqueada` 2 vezes → sai da fila e vai para `failures.md`.
- **Bônus contra deterioração**: cada tarefa é uma sessão curta; o contexto longo fica só no orquestrador, que lê arquivos, não históricos.

### 5.5 Qual escolher
| Situação | Ferramenta |
|---|---|
| Um objetivo grande, interativo, horas/dias | Codex TUI `/goal` (ou Claude `/goal`) |
| Lote repetitivo noturno | script + `codex exec`/`claude -p` com `timeout` + `flock` + `--max-turns` |
| Várias partes independentes ao mesmo tempo | Claude workflow / background agents |
| Esperar algo externo terminar | `/loop` dinâmico ou timer do systemd |
| Backlog que cresce, várias tarefas pequenas | Modo fila (§5.4) |
| Rodar todo dia sem a máquina ligada | routine na nuvem |

## 6. Guardrails (obrigatórios em toda execução longa)

1. **Portões humanos** escritos no `goal.md`: gasto de crédito, API paga, deploy/push em produção, e-mail, apagar dados, decisão de negócio.
2. **Tetos**: tempo (`timeout`), tokens (budget do goal quando houver), memória (cgroup/`systemd-run` — em máquinas de memória unificada o thrashing trava o host antes do OOM-killer).
3. **Detecção de estagnação**: 3 ciclos sem avanço no critério → parar, registrar, escalar.
4. **Processos**: não usar `pkill -f <padrão>` no mesmo comando que contém o padrão (mata o próprio shell); laços `pgrep` em arquivo de script.
5. **Saída de ferramenta curta**: é ela que incha o JSONL e o contexto. Gravar logs em arquivo e ler trechos (`tail -50`).
6. **Validar na prática** (abrir a página, rodar o script, medir) — não declarar pronto pela leitura do código.
7. **Deterioração de contexto** (vale para `/goal` no Codex e no Claude): agir por **faixas de uso do contexto**, antes do automático (~90–95%):
   - **~50%** → acrescentar no `canal.md` o que importa (fatos, aprendizados, glossário, armadilhas);
   - **~70%** → atualizar `state.md`/`progress.md`, terminar a unidade atual e rodar `/compact`;
   - **~85% ou 3ª compactação** → `/session-handoff`, sessão nova e `/prime` (ou releitura de `longrun/`).
   No Claude Code o `tools/hook-longrun.py` mede a % (mesma conta do statusline) e injeta o aviso uma vez por faixa, só com execução longa ativa; o aviso chega uma chamada de ferramenta depois, porque a transcrição é gravada com atraso. No Codex, acompanhar o % em `/status`. Após toda compactação ou retomada, reler goal → state → plan → canal. Sinal de que degradou: o agente repete o mesmo plano de fechamento sem fechar, ou reabre item já feito.
8. **Espera entre ciclos × cache**: se o orquestrador dorme entre ciclos, o intervalo fica **abaixo do TTL do cache** (OpenAI 30 min → acordar a cada ~25 min; Claude 1 h → ~55 min; Claude 5 min → não tentar). Acordar só para manter o cache compensa se houver trabalho previsto nas próximas horas (equilíbrio ≈ escrita ÷ leitura: ~12 a 25 acordadas); para pausas longas, deixar expirar ou fazer handoff. Pela assinatura o custo é cota, mas a conta é a mesma.

## 7. Observação e métricas

Por execução, registrar no `progress.md`:
- turnos, compactações, duração de parede;
- input / cached / output tokens e **cache ratio = cached ÷ input**;
- tamanho do JSONL e quanto é saída de ferramenta (métrica de diagnóstico, não limite: o arquivo grande não trava nada; o que pesa é o contexto);
- erros e retrabalho (linhas em `failures.md`);
- critério de pronto: atingido? em quanto tempo?

`python3 tools/medir-sessao.py <sessão.jsonl> [--json] [--por-turno]` extrai tudo isso dos JSONL do Codex (`~/.codex/sessions`) e do Claude Code (`~/.claude/projects`, deduplicando mensagens por id). Lê 1,8 GB em ~9 s. Os scripts crus antigos continuam em `tools/medicao/`.

**Atenção:** o Claude Code apaga as próprias transcrições após `cleanupPeriodDays` dias (padrão 30). Nesta máquina foi para **365** em 01/10/2026; quem quiser guardar por mais tempo arquiva antes com `tools/arquivar-sessoes.py`.

## 8. Fases de implantação

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **F0** ✅ | Este repo: material de origem, pesquisa, plano, templates | publicado |
| **F1 — piloto** ✅ | Execução longa real em `longrun/2026-10-01-medir-sessao/`: goal nível 3, 14 testes congelados, loop headless com `codex exec` (GPT-6 Astra) | **concluído no 1º ciclo** (3 min, 10 turnos, cache 91%); verificação independente: hash dos testes intacto, sem valores fixos, 14/14 reproduzido, sessão nunca vista confere |
| **F2 — medição** ✅ | `tools/medir-sessao.py` (entregue pelo piloto) | bate com o oráculo em 2 sessões grandes (1,8 GB Codex e 17 h Claude) + uma terceira não vista |
| **F3 — regras** ✅ | Bloco de `templates/AGENTS-long-run.md` em `~/.claude/CLAUDE.md` e `~/.codex/AGENTS.md` | sessão nova do Claude e do Codex responde "novo-longrun.sh + nível 3" sem ser lembrada |
| **F4 — rede de segurança** ✅ | `flock` + `timeout` nos 3 jobs do cron que chamam agente; `--max-turns` no `claude -p` do `resumir.py`; hook `tools/hook-longrun.py` (PreCompact, SessionStart `compact\|resume` e faixas de contexto em PostToolUse/UserPromptSubmit) + `canal.md`; `compact_prompt` estruturado no Codex | segunda instância sai na hora, timeout mata; numa sessão real com longrun ativo, o aviso chega após `/compact`, após retomar e ao cruzar a faixa (o agente escreveu no `canal.md` sozinho) |
| **F5 — vigia de agente** ✅ | `tools/vigia.py` + timer `longrun-vigia` (a cada 10 min): parado, parado sem aviso (lock solto), ociosa | 5 cenários testados; alerta forçado gravado em `~/.local/state/execucao-longa/alertas.log` + notify-send, sem repetir |
| **F6 — higiene** 🟡 | `tools/arquivar-sessoes.py` (relatório por padrão; `--aplicar` comprime com conferência sha256; `--restaurar`) | ida e volta sem perda testada; **não aplicado nas sessões reais** (só 0,04 GB > 90 dias; decisão do usuário) |
| **F7 — até onde vai** 🟡 | Curva retrospectiva em `docs/experimento-f7-retrospectivo-2026-10.md`; protocolo do experimento prospectivo (sessão única × modo fila) | retrospectiva feita (cache não cai com compactações; custo por turno cresce ~5x sem compactar); **prospectivo pendente** |

### Lições do piloto (01/10/2026)
- Com testes congelados e especificação precisa, o agente concluiu em **1 ciclo**: a maior parte do trabalho de uma execução longa é escrever o critério, não esperar.
- O teste que decide é do loop, não do agente: o loop roda o teste final e confere o hash dos testes. O agente não fez commit nem tocou nos testes.
- Verificar além do que o agente diz: hash dos testes, busca por valores fixos, rodar de novo e testar numa entrada nunca vista.
- Hooks de compactação só falam se houver longrun **ativo**; um teste com execução já concluída parece falha do hook, mas é o comportamento certo.
- O `/goal` interativo (TUI) não roda de dentro de uma sessão de agente; o piloto usou a receita headless (§5.2).

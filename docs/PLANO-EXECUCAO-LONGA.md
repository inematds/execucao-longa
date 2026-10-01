# Plano — como usar execuções longas (Codex + Claude Code)

Data: 01/10/2026. Base: material de origem (`docs/origem/`) e pesquisa web (`docs/pesquisa-web-2026-10.md`).

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
```

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
- O prompt aponta para os arquivos de estado; cada execução é um ciclo curto; o laço externo (script) decide se roda o próximo ciclo lendo `state.md` / resultado do teste.

### 5.3 Claude Code
- **`/goal <condição>`**: o avaliador só vê a conversa, então a condição deve ser algo que o agente **mostra** na saída (ex.: "a saída do `npm test` mostra 0 falhas").
- **Background agents / workflows**: para lotes paralelos de partes independentes; respeitar o teto de agentes simultâneos.
- **`/loop`** (dinâmico, com ScheduleWakeup): para **vigiar** algo externo (fila, render, CI), não para "trabalhar mais". Loops expiram em 7 dias.
- **Routines / `/schedule`** (nuvem): rodam fora da máquina — avaliar antes o que elas acessam.
- `claude -p` em cron: sempre com `timeout`, `flock` e `--max-turns`.

### 5.4 Qual escolher
| Situação | Ferramenta |
|---|---|
| Um objetivo grande, interativo, horas/dias | Codex TUI `/goal` (ou Claude `/goal`) |
| Lote repetitivo noturno | script + `codex exec`/`claude -p` com `timeout` + `flock` + `--max-turns` |
| Várias partes independentes ao mesmo tempo | Claude workflow / background agents |
| Esperar algo externo terminar | `/loop` dinâmico ou timer do systemd |
| Rodar todo dia sem a máquina ligada | routine na nuvem |

## 6. Guardrails (obrigatórios em toda execução longa)

1. **Portões humanos** escritos no `goal.md`: gasto de crédito, API paga, deploy/push em produção, e-mail, apagar dados, decisão de negócio.
2. **Tetos**: tempo (`timeout`), tokens (budget do goal quando houver), memória (cgroup/`systemd-run` — em máquinas de memória unificada o thrashing trava o host antes do OOM-killer).
3. **Detecção de estagnação**: 3 ciclos sem avanço no critério → parar, registrar, escalar.
4. **Processos**: não usar `pkill -f <padrão>` no mesmo comando que contém o padrão (mata o próprio shell); laços `pgrep` em arquivo de script.
5. **Saída de ferramenta curta**: é ela que incha o JSONL e o contexto. Gravar logs em arquivo e ler trechos (`tail -50`).
6. **Validar na prática** (abrir a página, rodar o script, medir) — não declarar pronto pela leitura do código.

## 7. Observação e métricas

Por execução, registrar no `progress.md`:
- turnos, compactações, duração de parede;
- input / cached / output tokens e **cache ratio = cached ÷ input**;
- tamanho do JSONL e quanto é saída de ferramenta;
- erros e retrabalho (linhas em `failures.md`);
- critério de pronto: atingido? em quanto tempo?

Scripts para extrair isso dos JSONL do Codex (`~/.codex/sessions`) e do Claude Code (`~/.claude/projects`) em `tools/medicao/` (versão crua).

## 8. Fases de implantação

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **F0** (feito) | Este repo: material de origem, pesquisa, plano, templates | publicado |
| **F1 — piloto** | Uma execução longa real com `/goal` usando `longrun/` + templates, num projeto com teste automático | goal concluído + `progress.md` com métricas + lições registradas |
| **F2 — medição** | `tools/medir-sessao.py <jsonl>` (Codex e Claude): turnos, compactações, cache ratio, bytes por tipo | bate com medição manual em 2 sessões grandes |
| **F3 — regras** | Bloco LONG-RUN (`templates/AGENTS-long-run.md`) nas instruções globais dos agentes | uma sessão nova segue o padrão sem ser lembrada |
| **F4 — rede de segurança** | `timeout` + `flock` + `--max-turns` nos jobs agendados com agente; hook antes de compactar/encerrar lembrando de salvar `state.md` | job travado não sobrepõe; hook dispara num teste |
| **F5 — vigia de agente** | Watchdog que avisa quando um goal fica bloqueado/sem cota ou a sessão para de gerar eventos por X min | alerta chega num teste forçado |
| **F6 — higiene** | Arquivar/comprimir sessões antigas (> 90 dias) | espaço liberado, nada ativo perdido |
| **F7 — experimento "até onde vai"** | Uma sessão contínua por dias medindo qualidade × cache × compactação × custo | curva por turno e ponto de corte recomendado |

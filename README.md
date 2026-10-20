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
3. Instale as skills `session-handoff` e `prime` do **[skillmanager3x](https://inematds.github.io/skillmanager3x/guia/)** ([repo](https://github.com/inematds/skillmanager3x); mesma versão do kit [agente-claude-codex](https://github.com/inematds/agente-claude-codex) 1.5.2): `cp -r skill/pt/session-handoff skill/pt/prime ~/.claude/skills/`. O hook só **pede** o handoff; quem grava (`handoff-grava.py`, `latest.md` como índice de abertos) e quem retoma (`/prime`) são essas skills. Desde a 1.5.2 o handoff se confere: o script grava o commit e o sha256 dos arquivos (`handoff-grava.py --conferir` acusa handoff velho), todo `[confirmed]` aponta commit, teste ou arquivo, e 5 perguntas-teste deixam o `/prime` mostrar quanto recuperou (N/5).
4. No `~/.claude/settings.json`, ligue `tools/hook-longrun.sh` em `PreCompact`, `SessionStart` (matcher `compact|resume|clear`), `PostToolUse`, `UserPromptSubmit` e `Stop`. Ele avisa o agente por **faixa de contexto**, medida sobre o **ponto em que o Claude Code compacta** (~967 mil nos modelos de 1M, como diz a documentação do Claude Code; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` ou `LONGRUN_TETO` mudam. As compactações de 200–575 mil vistas nos registros eram por **ociosidade**, ~55 min parado, não por tamanho): ~50% → anotar no `canal.md`; ~70% → atualizar o estado e `/compact`; ~85% → `/session-handoff` + sessão nova + `/prime`. Também manda reler o estado depois de compactar ou retomar. **Em qualquer sessão** (mesmo sem execução longa), em ~70% e ~85% pede ao agente que grave o handoff sozinho (skill `session-handoff`) e, depois de uma compactação, que releia o handoff recente junto com o resumo (ou grave um, se não houver; estudo em `docs/compactacao-x-handoff-2026-10-15.md`), enquanto o cache ainda está quente, e **confere** na transcrição se o arquivo foi gravado em `handoffs/history/` (cobra até 2 vezes e avisa "handoff conferido" ou "NÃO foi gravado"). Na 3ª compactação da sessão pede sessão nova. Depois de mais de 60 min parado com contexto acima de 150 mil, **bloqueia uma vez** a mensagem e avisa que o cache venceu (reenviar continua; `/clear` começa limpo e a sessão nova já aponta o último handoff). **Desde a 1.7.1** o aviso traz o comando com o handoff gravado **por esta sessão** (`/prime handoffs/history/<arquivo>.md`, lido da saída do `handoff-grava.py` na transcrição), porque outra sessão pode ter gravado um mais novo no mesmo projeto. **Handoff por ociosidade (1.5.1, evento `Stop`):** ao fim de cada resposta, com contexto ≥ 200 mil tokens e a pasta `handoffs/`, o hook só **agenda** (timer `systemd-run --user`, um por sessão, refeito a cada resposta) uma conferência para daqui a 45 min (desde a 1.9.6; era 30, e a compactação por ociosidade vem por volta dos 54 min). Se a sessão continuar parada, sem handoff recente e com o cache de 1 h valendo (< 55 min), ele grava o handoff numa **cópia** da sessão (`claude -p --resume --fork-session`, mesmo modelo, cache quente) que só pode rodar o `handoff-grava.py` e ler arquivos; registro em `~/.local/state/execucao-longa/ocioso.log`, e o aviso de cache vencido cita o handoff gravado. Quem está trabalhando não é mais interrompido: o pedido "Handoff contínuo" da 1.1–1.4 (a cada 30 min de trabalho) fica desligado (`LONGRUN_CONTINUO_TOKENS=200000` religa). **Desde a 1.8.2**, quem volta antes de 1 h (sem o bloqueio da pausa) vê na primeira mensagem uma linha, sem bloquear: "Handoff gravado sozinho às HH:MM… para recomeçar limpo: /clear e depois /prime <arquivo>". Aparece uma vez por handoff automático. Nos avisos, `/clear` e `/prime <arquivo>` vêm em linhas separadas (1.8.3). **Desde a 1.8.6** o resumo de ausência que o Claude Code grava quando você troca de foco (`away_summary`) e comandos locais como `/exit` não contam mais como "a sessão andou", e só vale como handoff recente o gravado até 5 min antes da última resposta (antes, um handoff de 30 min atrás deixava o fim do trabalho de fora). Ajustes: `LONGRUN_OCIOSO_MIN`, `LONGRUN_OCIOSO_TOKENS` (0 desliga), `LONGRUN_CACHE_MIN`. E ponha `"cleanupPeriodDays": 365` (o padrão de 30 dias apaga as transcrições). **Medição de retomada (1.6.1):** se o handoff mais novo do projeto tem a seção "Perguntas-teste" (kit agente-claude-codex 1.5.2+), depois de compactar, de `--resume` e no reenvio depois da pausa com cache vencido, o hook pede ao agente as 5 respostas **de memória, antes de abrir o handoff**; ele manda as respostas para `tools/nota-retomada.py`, que **dá a nota pelas chaves das perguntas** (1.10.6; antes o próprio agente se dava a nota), guarda as respostas para auditar e separa erro por handoff desatualizado (a fonte mudou) de informação perdida na retomada. Na sessão limpa, pede a nota do `/prime`. `python3 tools/nota-retomada.py --relatorio` mostra o acerto e o contexto por modo (compactada, retomada, continuada, prime); `LONGRUN_MEDIR=0` desliga. **Desde a 1.7.2** a medição de compactada, retomada e continuada usa só o handoff gravado **por esta sessão**; se ela não gravou nenhum, não pede nota (antes pegava o mais novo do projeto, que podia ser de outra sessão). **Índice de abertos (1.2.0):** com o `latest.md` no formato índice (gravado pelo `handoff-grava.py` da skill session-handoff, kit agente-claude-codex 1.4.1+, distribuída também pelo skillmanager3x), a sessão limpa lista todos os trabalhos abertos do projeto, não só o último; e avisa snapshot com carimbo no nome posterior à gravação (carimbo inventado).
5. Vigia: copie `tools/systemd/longrun-vigia.*` para `~/.config/systemd/user/` e rode `systemctl --user enable --now longrun-vigia.timer` (alerta execução parada ou ociosa).
6. Crons que chamam agente: `flock -n <lock> timeout <teto> <script>`.

## "Sessão parada há Xh: o cache venceu" — não é erro

Ao voltar para uma sessão parada há mais de 60 min com contexto acima de 150 mil tokens, o hook (`UserPromptSubmit`, função `pausa` em `tools/hook-longrun.py`) **segura a primeira mensagem uma vez**. O cache do prompt dura ~1 h; depois disso, a próxima mensagem relê a conversa inteira sem cache e gasta muito do limite. O aviso deixa você escolher antes de pagar.

Exemplo real (sessão parada há 5h33 com 220 mil tokens):

```
● UserPromptSubmit operation blocked by hook:
  Sessão parada há 5h33: o cache venceu e esta mensagem vai reprocessar ~220 mil tokens do seu limite.
  Para continuar aqui, reenvie a mensagem. Para começar limpo: /clear e depois /prime
  (o último handoff do projeto é indicado na abertura).

  Original prompt: ficou muito ruim, a movimentação da apresentação...
```

O que fazer:

- **Continuar nesta sessão:** reenvie a mesma mensagem. Passa direto (o bloqueio vale uma vez por pausa e fica gravado no estado da sessão).
- **Começar leve (recomendado):** `/clear` e depois `/prime`. A sessão nova lê o último handoff e repete o pedido com ~20 mil tokens em vez de 220 mil.

Cada sessão é contada à parte: duas sessões paradas mostram o aviso uma vez cada. Ajuste por variável de ambiente:

| Variável | Padrão | Efeito |
|---|---|---|
| `LONGRUN_PAUSA_MIN` | `60` | minutos parado antes de segurar (ex.: `120`) |
| `LONGRUN_PAUSA_TOKENS` | `150000` | contexto mínimo para segurar; `0` desliga a trava |

## Cache, handoff automático e compactação: como funciona

**Quanto custa voltar a uma sessão parada.** A cada mensagem, o Claude Code reenvia a conversa inteira. Com o cache quente (até ~1 h desde a última resposta), essa releitura sai por ~10% do preço normal de entrada. Depois de 1 h o cache vence: a próxima mensagem reprocessa tudo e grava o cache de novo (~2× o preço normal, cerca de 20× uma mensagem com cache quente). Numa sessão em 48% do contexto, são ~480 mil tokens relidos de uma vez. Na assinatura isso não vira dinheiro, mas sai da cota de uso (limite de 5 h e semanal). Paga-se uma vez só: as mensagens seguintes voltam a ser baratas.

**Por isso o handoff tem hora certa.** Gravado com o cache quente, o handoff custa uma mensagem barata. Pedido depois que o cache venceu, ele próprio paga a releitura cheia. O `/compact` custa o mesmo, porque também lê tudo. Se o trabalho já está em arquivos (commits, pendências, CLAUDE.md), dá para fazer `/clear` + `/prime` sem handoff, e sai barato, porque o prime lê só o necessário. Só vale pagar a releitura quando há decisões que ficaram apenas na conversa.

**Handoff automático por ociosidade.** O agente só roda quando chega uma mensagem, e os hooks disparam por evento, não por relógio: sem ajuda, nada grava o handoff enquanto você está em outra coisa. O `tools/hook-longrun.py` resolve isso no evento `Stop`:

1. Ao fim de cada resposta, com contexto ≥ 200 mil tokens (~20% da janela de 1M) e a pasta `handoffs/` no projeto, agenda um timer (`systemd-run --user`, um por sessão, refeito a cada resposta) para daqui a 45 min.
2. Quando o timer dispara, o hook confere três coisas: a sessão continua parada, não há handoff desta sessão gravado até 5 min antes da última resposta, e o cache ainda vale (< 55 min).
3. Se as três baterem, grava o handoff numa **cópia** da sessão (`claude -p --resume --fork-session`, mesmo modelo, pela assinatura). A cópia lê com o cache quente e só pode rodar o `handoff-grava.py` e ler arquivos. A sessão aberta não é tocada.
4. Cada conferência fica registrada em `~/.local/state/execucao-longa/ocioso.log` (gravou, ou por que não gravou).

**Linha do tempo de uma sessão parada:**

| Tempo parado | O que acontece |
|---|---|
| 0 | a resposta termina e o timer de 45 min é agendado |
| 3–12 min | se você trocou de foco, o Claude Code grava um "resumo de ausência" (`away_summary`) na conversa; isso **não** conta como atividade |
| 45 min | handoff gravado na cópia, com o cache quente |
| ~54 min | o Claude Code compacta sozinho por ociosidade (só acima de ~200 mil tokens), ainda com o cache quente |
| 60 min | o cache vence |
| ao voltar | se compactou: a conversa segue do resumo, barata, e o hook pede para reler o handoff junto. Se não compactou e passou de 60 min: o hook segura a primeira mensagem uma vez (seção anterior) e mostra `/clear` + `/prime <handoff desta sessão>` |

**Por que 45 min e não 50.** A compactação por ociosidade vem entre 53 e 58 min, e a cópia leva 30–60 s mais a partida do Claude. Aos 50 min ela pode chegar depois do resumo ou passar do limite de 55 min do cache. O custo é o mesmo a qualquer hora antes de 1 h (uma leitura com o cache quente); 45 deixa folga.

**A compactação automática não substitui o handoff.** O resumo perde detalhe (decisões, arquivos, o que não fazer), e ela nem sempre acontece. Em 18/10/2026, uma sessão parada com 480 mil tokens não foi compactada, e a volta pagou a releitura cheia. O handoff aos 45 min é a proteção; a compactação é bônus quando vem.

**O que já fez o handoff automático falhar** (corrigido na 1.8.5 e na 1.8.6):

- **Data do arquivo.** O Claude Code acrescenta linhas sem carimbo depois da resposta, e o hook lia isso como "a sessão andou". Agora ele decide pela última linha com carimbo.
- **Troca de foco e `/exit`.** O `away_summary` e os comandos locais têm carimbo e também pareciam atividade: 7 sessões de 16/10 ficaram sem handoff. Agora só contam mensagens do usuário e respostas do agente.
- **Handoff velho contando como recente.** Um handoff das 07:38 cobria uma resposta das 08:06, e a meia hora final se perdia. Agora só vale o handoff gravado até 5 min antes da última resposta. Se o cache vencer com um handoff automático anterior ao último trabalho, o aviso diz isso, em vez de "nenhum handoff".

| Variável | Padrão | Efeito |
|---|---|---|
| `LONGRUN_OCIOSO_MIN` | `45` | minutos parado antes de gravar (não passe de ~45) |
| `LONGRUN_OCIOSO_TOKENS` | `200000` | contexto mínimo para gravar; `0` desliga |
| `LONGRUN_CACHE_MIN` | `55` | depois disso a cópia não roda (o cache já estaria frio) |

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
| [`tools/hook-longrun.sh`](tools/hook-longrun.sh) | Hook do Claude Code: faixas de contexto (50/70/85% do ponto de compactação), handoff conferido, aviso de cache vencido, salvar antes de compactar e reler depois |
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

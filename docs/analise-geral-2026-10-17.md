# Análise geral — não perder o contexto em trabalho longo (17/10/2026)

Base: material de origem (`docs/origem/`), pesquisas de 01/10, estudo compactação × handoff de 15/10, medições de 17/10 nas transcrições desta máquina e o código do hook, do kit `agente-claude-codex` e do skillmanager3x nesta data.

---

## 1. Resumo

- O problema de "perder o contexto" são **três problemas diferentes**, cada um com uma solução:
  - **cache:** a conta de reprocessar o que já foi lido;
  - **compactação:** o resumo que perde detalhe;
  - **continuidade:** o trabalho sobreviver a `/clear`, a uma queda ou à troca de modelo.
- O sistema tem **três camadas**:
  - **contexto ao vivo:** a sessão atual;
  - **handoff:** o estado da tarefa, gravado em arquivo;
  - **memória persistente:** regras e fatos que valem sempre.
  - Atrás delas fica o **histórico** só-acrescenta (handoffs antigos, decisões, git), consultado quando precisa.
- Em 17/10 o handoff passou a **se conferir sozinho**:
  - o script grava o commit e a impressão digital dos arquivos;
  - todo `[confirmed]` aponta uma prova;
  - 5 perguntas-teste medem quanto foi recuperado;
  - o hook passou a registrar essa nota em cada forma de retomar.
- Medido: voltar por `/clear` + `/prime` custa ~187 mil tokens-equivalentes, contra ~284 mil para reenviar numa sessão grande com o cache vencido. Daí em diante, ~10 mil por turno contra ~23 mil. **Quanto conhecimento cada caminho preserva começa a ser medido agora.**

---

## 2. Os três problemas

| Problema | O que é | Quando dói | Solução no sistema |
|---|---|---|---|
| **Cache** | O provedor guarda o começo do prompt já processado; reaproveitar custa 0,1x, reprocessar custa 1,25x–2x | Depois de uma pausa maior que o tempo de vida do cache | Hook bloqueia uma vez e explica: reenviar (relê tudo) ou `/clear` + `/prime` |
| **Compactação** | O histórico antigo vira um resumo | Em toda compactação; piora a cada uma | Handoff gravado antes, relido depois do resumo; faixas de contexto para compactar cedo |
| **Continuidade** | O trabalho seguir em outra sessão, outro dia ou outro modelo | `/clear`, queda, troca Claude ↔ Codex | Handoff em arquivo + `/prime`; índice de trabalhos abertos por assunto |

Números de referência:
- Cache entre 93% e 99% em todas as sessões longas medidas. Ele **não piora** com o número de compactações; não é motivo para cortar a sessão.
- Sem compactar, o custo por turno cresce: no Claude 1M, o último décimo da sessão lê ~5x mais por turno que o primeiro.
- Metade de um JSONL de 1,84 GB era saída de ferramenta. O tamanho do arquivo não pesa; o que pesa é o contexto ativo.

---

## 3. Como cada ferramenta lida com isso

### 3.1 Claude Code

| Mecanismo | Como funciona aqui |
|---|---|
| Cache | Vale 5 min ou 1 h (o Claude Code usa 1 h). Ler do cache = 0,1x; regravar = 2x com 1 h |
| Compactação por tamanho | ~967 mil tokens nos modelos de 1M (`CLAUDE_CODE_AUTO_COMPACT_WINDOW` muda) |
| Compactação por ociosidade | ~55 min sem resposta, só acima de ~200 mil: compacta antes do cache vencer. Nos registros de 07–15/10, todas as 93 compactações vieram por ociosidade, nenhuma por tamanho |
| `/goal` | Um modelo pequeno avalia a condição a cada turno, **lendo só a conversa**. A condição tem de ser algo que o agente mostra na saída |
| `/loop`, background agents, workflows, routines | Vigiar algo externo, paralelizar partes, rodar na nuvem |
| Hooks | Existem (PreCompact, SessionStart, PostToolUse, UserPromptSubmit, Stop). É neles que o `hook-longrun` trabalha |
| Transcrições | Apagadas após `cleanupPeriodDays` (padrão 30; aqui 365) |

### 3.2 Codex

| Mecanismo | Como funciona aqui |
|---|---|
| Cache | Vale ~30 min. Perder custa até 25x no GPT-6.1 Sol |
| Compactação | Automática perto de 90–93% da janela (~230–240 mil de 258 mil): tarde para a qualidade do resumo. Com modelo da OpenAI ela roda no servidor e **ignora o `compact_prompt`**; o prompt estruturado em `~/.codex/config.toml` só vale no `/compact` manual |
| GPT-6 Astra | Guarda notas entre janelas de contexto em vez de um resumo único. Ajuda, mas não substitui o estado em arquivo |
| `/goal` (TUI) | `/goal`, `/goal pause\|resume\|clear`, `/goals`. Retoma depois do limite de uso e do reinício do daemon |
| `codex exec` | Modo sem interface para lotes: stdin fechado, `timeout`, `flock`, `MemoryMax` |
| Hooks | Não há PreCompact/PostCompact nem contador de compactações. O controle é manual: `/status` mostra o %, e o agente segue as regras do `AGENTS.md` |
| Skills | `session-handoff` e `prime` instaladas em `~/.agents/skills` (as mesmas do Claude) |

**Diferença prática:** no Claude o hook faz o trabalho de vigiar e pedir o handoff, conferir e medir. No Codex quem faz isso é a regra escrita no `AGENTS.md` mais você. O handoff e o `/prime` funcionam igual nos dois, e um lê o que o outro gravou.

---

## 4. O nosso sistema

### 4.1 As camadas

| Camada | O que guarda | Onde | Quem escreve | Quando é lida |
|---|---|---|---|---|
| Contexto ao vivo | Tudo da sessão atual | Na sessão (e no resumo, depois de compactar) | O próprio trabalho | Sempre |
| Handoff | Estado da tarefa: feito com prova, pela metade, decisões, próxima ação, perguntas-teste | `handoffs/history/<UTC>-<assunto>.md` + índice em `handoffs/latest.md` | Skill `session-handoff` pelo `handoff-grava.py` | `/prime`, depois de compactar, sessão limpa |
| Memória persistente | Regras e fatos que valem sempre | `CLAUDE.md`/`AGENTS.md`, `LESSONS.md`, memória do runtime, `canal.md` | Agente quando é corrigido ou descobre algo durável | Toda sessão (carregada) |
| Histórico | Tudo que aconteceu, datado, só-acrescenta | `handoffs/history/`, `decisions.md`, `progress.md`, `failures.md`, `FALHAS.md`, git log | Agente e scripts | Sob demanda |

**Regra de decisão:** se continua verdade depois que a tarefa acaba, vai para a memória persistente. Se é estado desta tarefa, vai no handoff. Se é registro do que aconteceu, vai no histórico.

**E o histórico das sessões (JSONL)?** Não é fonte:
- metade é saída de ferramenta;
- é apagado após o prazo;
- o Codex não lê o do Claude;
- o `/prime` proíbe usá-lo.

O comando `recall` busca nele para lembrar de algo (índice de 7 mil sessões, resposta em 0,02 s), mas o que foi decidido tem de estar num arquivo do projeto. O git é o único histórico que o agente não reescreve.

### 4.2 Handoff normal (qualquer sessão)

```
trabalho → handoff (arquivo) → /clear → /prime → trabalho
                ↑                          ↓
        compactação: relê o handoff   confere frescor, provas e perguntas-teste
```

1. **Gravar.** A skill `session-handoff` monta o texto num modelo fixo:
   - projeto e escopo, objetivo, estado aceito (`[confirmed]` com prova);
   - proposto e não confirmado, decisões, arquivos, memória tocada;
   - verificação (só o que rodou), estado em execução;
   - perguntas abertas, próxima ação, mapa de retomada, **perguntas-teste**, checagem de compartilhamento.
2. **O script grava**, e não o agente:
   - carimbo real do relógio, arquivo novo que nunca é sobrescrito;
   - índice de trabalhos abertos por assunto no `latest.md`;
   - **bloco de estado** (commit + sha256 dos arquivos);
   - commit só desses arquivos, sem push.
3. **Quem pede o handoff:**
   - você;
   - o hook nas faixas de 70% e 85% do contexto, depois de compactar e por ociosidade. Ociosidade: 30 min parado com ≥ 200 mil, gravado numa cópia da sessão com o cache ainda quente, sem interromper ninguém.
4. **Depois de compactar:** o hook manda reler o handoff junto com o resumo. A compactação guarda mais detalhe (arquivos, passos); o handoff guarda o que foi provado, as decisões e a próxima ação.
5. **Pausa longa:** com o cache vencido e mais de 150 mil no contexto, o hook bloqueia uma vez. Reenviar continua; `/clear` começa limpo, e a sessão nova já lista os trabalhos abertos.
6. **Retomar com `/prime`:**
   - lê `AGENTS.md`/`CLAUDE.md`, contexto, tarefa e handoff, sem editar e sem rodar código;
   - confere com o git;
   - devolve um resumo com fonte em cada linha, incluindo frescor, provas e nota das perguntas-teste.

### 4.3 Execução longa

Para um objetivo grande, com condição de pronto testável:

1. `tools/novo-longrun.sh <projeto> <slug>` cria a pasta `longrun/<data>-<slug>/`:

| Arquivo | Guarda |
|---|---|
| `goal.md` | objetivo e critério de pronto no **nível 3+** (comando → saída esperada, com trava contra atalho: contagem mínima, testes congelados, validador) |
| `plan.md` | estratégia e os próximos 3 passos (reescrito) |
| `state.md` | o que funciona, o que falta, como retomar |
| `progress.md` | checkpoints com hash do commit (só acrescenta) |
| `failures.md` | erro → tentativa → resultado (só acrescenta) |
| `decisions.md` | decisão → motivo → alternativa descartada (só acrescenta) |
| `canal.md` | fatos, aprendizados, glossário, armadilhas: o que a compactação perde |

2. **Faixas de contexto** (o hook avisa uma vez cada):
   - ~50%: escrever no `canal.md`;
   - ~70%: atualizar o estado, gravar o handoff e `/compact`;
   - ~85%: handoff; sessão nova e `/prime` ao fim da unidade em curso.
3. **Depois de compactar ou retomar:** reler goal → state → plan → canal → fim de progress/failures, e seguir do primeiro item pendente.
4. **Sem interface** (`tools/loop-longrun.sh`):
   - cada ciclo é um `codex exec` ou `claude -p` com `flock`, `timeout` e `MemoryMax`;
   - **o loop roda o teste e confere o hash dos testes congelados**, não confia no agente;
   - ciclo que mexer em teste protegido é revertido;
   - para depois de 3 ciclos sem avanço.
5. **Modo fila:** backlog de tarefas `tasks/NNN.md`; fechar exige evidência; teto de tarefas novas por execução; acaba quando a fila esvazia.
6. **Portões humanos** escritos no `goal.md`: crédito, API paga, deploy, envio, apagar dados, decisão de negócio.

Piloto: com critério nível 3 e 14 testes congelados, a execução terminou no 1º ciclo (3 min). **A maior parte do trabalho é escrever o critério.**

### 4.4 Ferramentas de apoio

| Ferramenta | Faz |
|---|---|
| `tools/hook-longrun.py` | Faixas, pedido e conferência do handoff, bloqueio da pausa, handoff por ociosidade, **medição de retomada** |
| `tools/medir-sessao.py` | Turnos, tokens, cache e compactações de qualquer JSONL do Codex ou do Claude (1,8 GB em ~9 s) |
| `tools/custo-retomada.py` | **Novo:** custo real de reenviar com o cache vencido × `/prime` |
| `tools/nota-retomada.py` | **Novo:** registra e compara a nota das perguntas-teste por modo de retomar |
| `tools/recall.py` | Busca em tudo o que já foi dito com Codex e Claude |
| `tools/vigia.py` | Avisa agente parado ou ocioso (a cada 10 min) |
| `tools/arquivar-sessoes.py`, `faxina-claude-mem.py` | Higiene das transcrições e da memória do claude-mem |

---

## 5. Implementações novas (17/10/2026)

### 5.1 Kit `agente-claude-codex` 1.5.2 → 1.5.3 (as skills nascem aqui)

1. **Bloco de estado gravado pelo script.** Cada handoff termina com o commit atual e o sha256 dos arquivos citados e dos não commitados. O agente não escreve esse bloco; se escrever, o script descarta.
2. **`handoff-grava.py --conferir <handoff>`** (só leitura):
   - 0 = nada mudou;
   - 2 = mudou, com a lista;
   - 3 = handoff antigo sem bloco.

   Commit novo com o mesmo conteúdo não conta como mudança: o commit do próprio handoff e o trabalho pendente salvo depois.
3. **Prova em todo `[confirmed]`:** `commit`, `teste:` ou `arquivo:`. Sem prova, vira `[unverified]`.
4. **Perguntas-teste** no fim de todo handoff, com a fonte num arquivo do projeto, nunca no próprio handoff:
   - tarefa e critério de pronto;
   - última decisão e por quê;
   - o que não pode mudar;
   - o que está pela metade;
   - próxima ação.
5. **`/prime`** ganhou três passos e três linhas no resumo:
   - **frescor:** roda o `--conferir`;
   - **provas:** confere commit e arquivo de cada `[confirmed]`;
   - **perguntas-teste:** responde pelos arquivos, compara e mostra N/5.

   O que diverge não vira ação sem você confirmar.
6. 1.5.3: um arquivo ilegível não derruba mais a gravação; fica marcado como `ilegivel`.

**Verificação:**
- 23 testes do script passam.
- Teste ponta a ponta com o script instalado: "igual" logo após gravar, "divergente" ao mudar o arquivo citado.
- Instalado no Claude (`~/.claude/skills`) e no Codex (`~/.agents/skills`), com backup.
- Cópias PT e EN e docs PT/EN/ES no skillmanager3x.

### 5.2 `hook-longrun` 1.6.1 (execucao-longa)

- **Medição de retomada.** Se o handoff mais novo tem perguntas-teste, o hook pede as 5 respostas **de memória, antes de abrir o handoff**, em três momentos:

| Modo | Quando |
|---|---|
| `compactada` | Logo depois da compactação |
| `retomada` | Depois de `claude --resume` |
| `continuada` | No reenvio que passa pelo bloqueio da pausa (sessão antiga, cache vencido) |
| `prime` | Sessão limpa: o hook pede para registrar a nota do passo de perguntas-teste do `/prime` |

- O agente mostra as 5 respostas, abre o handoff e as fontes, marca certas e erradas e registra com `nota-retomada.py`. `nota-retomada.py --relatorio` compara os modos (acerto % e contexto mediano). `LONGRUN_MEDIR=0` desliga.
- **Verificação:** 64 testes do execucao-longa passam (7 novos). O hook instalado é o arquivo do repo, então já vale nesta máquina.

---

## 6. Medições

| Medição | Resultado | Fonte |
|---|---|---|
| Voltar a trabalhar, 14 dias, 4.609 transcrições | Reenviar com cache vencido: mediana 284 mil eq (190 casos, 17 mil–1,25 milhão), depois ~23 mil/turno. `/clear` + `/prime`: mediana 187 mil eq (11 casos), depois ~10 mil/turno | `tools/custo-retomada.py` |
| Compactação × handoff (17 casos) | Resumo da compactação: 20–54 arquivos citados. Handoff: 1–27, mas separa provado de palpite, guarda decisões e próxima ação, e sobrevive a `/clear` | `docs/compactacao-x-handoff-2026-10-15.md` |
| Sessão nova redescobre | 80% dos primeiros 25 passos são leituras (51–59% depois de compactar) | idem |
| Cache ao longo da sessão | 93–99%, não cai com compactações | `docs/experimento-f7-retrospectivo-2026-10.md` |

Ressalvas:
- O `/prime` tem só 11 casos.
- Parte das 190 retomadas pode ter passado por compactação antes.
- O piso de ~187 mil do `/prime` vem de regravar todo o pacote inicial (instruções, memória, skills) numa sessão nova.

---

## 7. Limites e o que falta

- **A nota é dada pelo próprio agente.** As 5 respostas ficam escritas antes de ele abrir o handoff, o que dá para auditar, mas não é uma checagem independente.
- **Com mais de 200 arquivos pendentes,** a lista do bloco de estado é cortada, e o `--conferir` acusa os que sobraram como mudança.
- **No Codex não há hook:** a medição e o pedido de handoff dependem da regra escrita e de você.
- **Experimento retomar × `/prime`:** os dados começam a entrar agora. Com ~1 semana de notas, `--relatorio` + `custo-retomada.py` dão custo **e** conhecimento lado a lado. É o experimento F7 do plano.
- **Decisões como entradas datadas** apontando a que substituem, em vez de reescrever a regra: ainda não implementado.
- O guia do kit `agente-claude-codex` (páginas PT/EN/ES) ainda não descreve a 1.5.2.

---

## 8. Respostas às perguntas da discussão

**Como saber se o agente recuperou o contexto certo?**
Três checagens que não dependem de confiar no agente:
1. **frescor:** o script compara o commit e os arquivos de quando o handoff foi gravado com os de agora;
2. **provas:** cada item confirmado aponta commit, teste ou arquivo, e o `/prime` confere;
3. **perguntas-teste:** quem retoma responde as 5 pelos arquivos e compara; o que não bate não vira ação sem confirmação.

**E se o handoff estiver velho?**
O `--conferir` acusa o que mudou depois que ele foi gravado. Nesse caso o handoff vale como pista, não como fato.

**O handoff não se autocertifica?**
Sim, e por isso a prova saiu do texto: o bloco de estado é gravado pelo script, e os itens confirmados apontam para git, teste ou arquivo. Na execução longa, quem decide se acabou é o teste rodado pelo loop, com hash dos testes congelados.

**Ponteiro ou texto corrido?**
Ponteiro: mapa de retomada, fontes das perguntas-teste e evidências são caminhos e commits. Isso sobrevive a compactação, sessão nova e troca de modelo.

**Deixar a compactação automática rodar?**
Sim. Dentro da mesma sessão ela guarda mais detalhe que o handoff. O handoff continua porque é o único que sobrevive a perder a sessão. Os dois juntos são melhores que qualquer um sozinho.

**O Claude já compacta sozinho depois de 1 h parado?**
Compacta com ~55 min parado, mas só acima de ~200 mil tokens. Abaixo disso o cache vence sem compactar, e é para essa faixa que serve o aviso de cache vencido.

**Quanto o `/clear` + `/prime` economiza em relação a recarregar tudo?**
Medido: ~100 mil tokens-equivalentes para voltar e ~13 mil por turno daí em diante.

**Quanto conhecimento se perde em cada caminho?**
É o que a nota das perguntas-teste mede agora, registrada separadamente para compactada, retomada, continuada e `/prime`.

**O que vai para a memória persistente e o que fica no handoff?**
Continua verdade depois da tarefa → memória persistente. Estado desta tarefa → handoff. Registro do que aconteceu → histórico.

**O histórico não é importante?**
É, e existe em três lugares confiáveis: handoffs antigos, arquivos de decisões/progresso/falhas e git. As transcrições das sessões servem para busca, não como fonte.

**O que deve ter no handoff?**
Decisões, estado com prova, o que está pela metade, a próxima ação e ponteiros para os arquivos, num modelo fixo. Histórico longo enterra o que o próximo agente precisa fazer.

**Medir por uma semana?**
É o próximo passo: `nota-retomada.py --relatorio` mais `custo-retomada.py`, depois de uma semana de uso.

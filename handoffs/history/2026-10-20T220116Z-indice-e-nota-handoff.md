# Handoff — índice do handoff (trava, parados, fechados, latest leve) e nota da retomada pelo script

## Projeto e escopo
- Sessão aberta em `~/projetos/execucao-longa`, mas o código do handoff vive em `~/projetos/agente-claude-codex` (kit; skills session-handoff e prime). Cópias: `~/.claude/skills`, `~/.agents/skills`, `~/projetos/dsh-skills`, `~/projetos/openpcbotv3/skills`, `~/projetos/skillmanager3x/skill/{pt,en}`.
- Origem: comentários do Skool que o Nei trouxe (índice crescendo com vários terminais; avaliador independente; "o script que gera a transferência").

## Objetivo atual
- Concluído. Nenhuma tarefa aberta nesta frente; só observar as notas novas da retomada.

## Estado aceito
- [confirmed] Kit 1.9.3: `flock` na pasta handoffs/history/ durante leitura→gravação→commit do índice; assunto sem handoff há mais de 3 dias vai para "Parados" (teto 50). Commit 3c82a86 no agente-claude-codex.
- [confirmed] Kit 1.10.3: `handoffs/fechados.md` (slug · snapshot · data · título), `--fechados`, `--recuperar-fechados` (pelo git log), `--arrumar`. Commit 740e6c5.
- [confirmed] Kit 1.11.3: `latest.md` = índice + ponteiro "Mais recente", sem cópia integral. Commit 338fa53. Medido: wifi 19,9 → 4,8 KB; reel7etapas 22,2 → 0,7 KB.
- [confirmed] Kit 1.12.3: perguntas-teste com `— chave:`; aviso no handoff-grava; prime 6c manda respostas ao script. Push feito (main = origin/main).
- [confirmed] execucao-longa: `tools/nota-retomada.py --respostas` dá a nota pelas chaves, guarda respostas e separa desatualizado × não recuperou; hook-longrun 1.10.6 (VERSAO em `tools/hook-longrun.py`); `tests/test_nota_retomada.py` (5 testes); 78 testes passam; push feito.
- [confirmed] `--arrumar` rodado e commitado/pushado em 11 projetos com índice (wifi, eventosextremospub, r7ex, reel7etapas, agentic-app, multiplayer-agentic, robotica-real2sim, robotica-so101, sala-multiplayer, execucao-longa). wifi pushado com os 5 commits de outras sessões (autorizado pelo Nei).
- [confirmed] Skills instaladas iguais ao dist em claude/codex/dsh/v3; openpcbotv3 e skillmanager3x (PT + EN traduzido pelo inema-traduz) com push.

## Proposto / tentado, não confirmado
- Nenhum.

## Decisões
- Estado do handoff é gravado pelo script; intenção (decisões, Não fazer, próxima ação) continua escrita pelo agente; o script confere o que dá para conferir. Fonte: resposta ao Nei nesta sessão e `README.md` do kit.
- Notas antigas (`--acertos`) ficam como "autoavaliadas", fora da média do relatório. Fonte: `tools/nota-retomada.py`.
- Item 4 (sorteio semanal de 2 medições para revisão humana) ficou para depois, por decisão do Nei.

## Não fazer (restrições e travas)
- Não fazer push de commits de outras sessões sem o Nei autorizar (ele autorizou só o do wifi, 20/10). Fonte: dito pelo usuário em 20/10, só nesta conversa.
- Não usar API para tradução; usar `inema-traduz` (assinatura). Fonte: `~/.claude/CLAUDE.md`.
- Não apagar snapshots de handoffs/history/. Fonte: skill session-handoff, regra 2.
- Não mexer nos arquivos sujos do openpcbotv3 (CLAUDE.md, FALHAS.md, config/ollama.yaml etc.): são de outra sessão. Fonte: `git status` do openpcbotv3 em 20/10.
- Não rodar `gh auth refresh -s workflow`. Fonte: `~/.claude/CLAUDE.md`.

## Pela metade
- Nada em código.
- Dois projetos ainda com `latest.md` no formato antigo (cópia, sem índice): agente-claude-codex e treinador-carisma. Não migrados.

## Arquivos alterados (execucao-longa)
- `tools/nota-retomada.py`, `tools/hook-longrun.py`, `tests/test_nota_retomada.py`, `README.md`, `README.en.md`, `README.es.md`, `FALHAS.md`, `CLAUDE.md` (lição de contagem do índice).

## Memória e regras duráveis tocadas
- `CLAUDE.md` do execucao-longa: lição "contar assuntos só dentro do bloco do índice".

## Verificação
- `python3 -m pytest -q tests/` no execucao-longa → 78 passed.
- `python3 -m pytest -q tests/` no agente-claude-codex → 43 passed; `tests/test-sync-skills.sh` → 20 passaram.
- `python3 tools/nota-retomada.py --relatorio` → tabela por modo + linha "autoavaliadas" (8 antigas).

## Estado em execução
- Nenhum processo em segundo plano.

## Perguntas abertas e adiados
- Migrar agente-claude-codex e treinador-carisma para o formato de índice? (não perguntado ainda de forma direta)
- Item 4: sorteio semanal de 2 medições para revisão humana — adiado.
- Experimento F7 (retomar × /prime) depende de ~2 semanas de notas novas pelo script.

## Próxima ação exata
- Nenhuma automática. Quando houver notas novas, rodar `python3 tools/nota-retomada.py --relatorio` e comparar modos (F7). Por quê: só as notas do script valem para a comparação. Precisa de aprovação: não (só leitura).

## Mapa de retomada
- `tools/nota-retomada.py` — nota pelo script, formato das chaves.
- `tests/test_nota_retomada.py` — comportamento esperado.
- `FALHAS.md` — linha de 20/10 com o motivo.
- `/home/nmaldaner/projetos/agente-claude-codex/CHANGELOG.md` — 1.9.3 a 1.12.3.

## Perguntas-teste
1. Qual é a tarefa atual e o critério de pronto? → nenhuma aberta; tudo pushado — fonte: `FALHAS.md` — chave: `nenhuma`
2. Qual foi a última decisão e por quê? → nota da retomada dada pelo script pelas chaves, porque a do agente não era auditável — fonte: `tools/nota-retomada.py` — chave: `script`
3. O que não pode mudar (restrição do usuário ou trava)? → não apagar snapshots de handoffs/history — fonte: `README.md` — chave: `snapshot` | `history`
4. O que está pela metade? → migrar latest.md antigo de agente-claude-codex e treinador-carisma — fonte: só nesta conversa — chave: `treinador-carisma`
5. Qual é a próxima ação, por quê, e ela precisa de aprovação? → rodar nota-retomada --relatorio com notas novas (F7), sem aprovação — fonte: `tools/nota-retomada.py` — chave: `relatorio` | `relatório`

## Checagem de compartilhamento
- Sem segredos, tokens, cookies ou dados pessoais: sim.


<!-- handoff-estado:inicio -->
## Estado gravado pelo script (não editar)

Gravado por handoff-grava.py no momento do handoff. `--conferir` compara com o projeto agora.

- commit: 569477e9491fdb4f1a9f54cfb88969a530fcf211 · branch: main
- arquivos sujos fora de handoffs/: 0
- `tools/hook-longrun.py` · sha256:031d887b585e · citado
- `tests/test_nota_retomada.py` · sha256:a0663a765d61 · citado
- `README.md` · sha256:f9896aec93a2 · citado
- `tools/nota-retomada.py` · sha256:9e2b2e0ef76c · citado
- `README.en.md` · sha256:2836d450a754 · citado
- `README.es.md` · sha256:9ed0c821ebdb · citado
- `FALHAS.md` · sha256:cebac9c7ca4d · citado
- `CLAUDE.md` · sha256:54bbd4fb8a5f · citado

### Repo do trabalho: /home/nmaldaner/projetos/agente-claude-codex
- commit: c5d69d6efedf2246338a5f01f4ccf8f007c9ad46 · branch: main
- arquivos sujos: 0
- impressão de todos os sujos: e3b0c44298fc1c14
<!-- handoff-estado:fim -->

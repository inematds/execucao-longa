# Handoff — 2026-10-17 — handoff que se confere (kit 1.5.3) + medição de retomada (hook 1.6.1) + análise geral

## Projeto e escopo
~/projetos/execucao-longa (e kits ligados ~/projetos/agente-claude-codex, ~/projetos/skillmanager3x). Pedido: responder as perguntas do post sobre contexto em execução longa, implementar frescor/provas/perguntas-teste no handoff, medir retomada no hook e escrever análise geral sem citar nomes.

## Objetivo atual
Concluído. Pendente só coletar dados: ~1 semana de notas para comparar modos (critério: `nota-retomada.py --relatorio` com medições em compactada e prime).

## Estado aceito
- [confirmed] Bloco de estado + `--conferir` no handoff-grava.py — evidência: commit 330ecb6 e 3640f56 em ~/projetos/agente-claude-codex
- [confirmed] Perguntas-teste e prova em [confirmed] nas skills; prime confere — evidência: arquivo: ~/projetos/agente-claude-codex/skills/prime/definition.md
- [confirmed] Hook 1.6.1 mede retomada; nota-retomada.py e custo-retomada.py — evidência: commit a44c74d; teste: `python3 -m pytest -q tests` → 64 passed
- [confirmed] Análise geral — evidência: arquivo: `docs/analise-geral-2026-10-17.md` (commit 281aa81)

## Proposto / tentado, não confirmado
- [unverified] Medição real em sessão: nenhuma nota registrada ainda — depende de handoffs novos com Perguntas-teste

## Decisões e restrições
- Skills nascem no agente-claude-codex (polyskill: definition.md → dist/); skillmanager3x só copia (EN traduzido à mão).
- Nota é autoavaliada pelo agente, com respostas escritas antes de abrir o handoff (auditável, não independente).
- Commit com mesmo conteúdo não conta como divergência no --conferir.

## Arquivos alterados
- `tools/hook-longrun.py`, `tools/nota-retomada.py`, `tools/custo-retomada.py`, `tests/test_hook_longrun.py`, `README.md`, `README.en.md`, `README.es.md`, `guia/`, `docs/analise-geral-2026-10-17.md`
- Fora do projeto: `~/projetos/agente-claude-codex/` (1.5.3), `~/projetos/skillmanager3x/skill/` (9ac8331, 739fa24), `~/.claude/skills/{session-handoff,prime}`, `~/.agents/skills/{session-handoff,prime}` (instaladas com backup)

## Memória e regras duráveis tocadas
- nenhuma

## Verificação
- Rodado: `python3 -m pytest -q tests/test_handoff_grava.py` (agente-claude-codex) → 23 passed
- Rodado: `python3 -m pytest -q tests` (execucao-longa) → 64 passed
- Rodado: `bash tests/test-sync-skills.sh` → 20 passaram
- Não rodado: medição real numa compactação — não houve compactação depois da instalação

## Estado em execução
- Processos em segundo plano: nenhum
- Servidores / portas: nenhum
- Worktrees / branches abertos: nenhum

## Perguntas abertas e adiados
- Adiado: guia PT/EN/ES do agente-claude-codex não descreve a 1.5.2 — só README/CHANGELOG
- Adiado: decisões como entradas datadas apontando a que substituem

## Próxima ação exata
Daqui a ~1 semana: `python3 tools/nota-retomada.py --relatorio` + `python3 tools/custo-retomada.py 7` e escrever a tabela custo × nota (experimento F7). Não precisa de aprovação.

## Mapa de retomada
- `docs/analise-geral-2026-10-17.md` — visão completa e limites
- `tools/hook-longrun.py` — medição de retomada (pedido_medir)
- `tools/nota-retomada.py` — registro e relatório

## Perguntas-teste
1. Qual é a tarefa atual e o critério de pronto? → coletar notas por 1 semana e comparar custo × nota — fonte: `docs/analise-geral-2026-10-17.md`
2. Qual foi a última decisão e por quê? → nota autoavaliada com respostas escritas antes de abrir o handoff, por ser auditável — fonte: `tools/nota-retomada.py`
3. O que não pode mudar? → skills se editam no agente-claude-codex (definition.md), nunca direto no dist/ ou nas cópias — fonte: commit 330ecb6
4. O que está pela metade? → guia do agente-claude-codex sem a 1.5.2 — fonte: `docs/analise-geral-2026-10-17.md`
5. Qual é a próxima ação e ela precisa de aprovação? → rodar --relatorio e custo-retomada em ~1 semana, sem aprovação — fonte: `docs/analise-geral-2026-10-17.md`

## Checagem de compartilhamento
- Sem segredos, tokens, cookies, dados pessoais ou endpoints privados: sim


<!-- handoff-estado:inicio -->
## Estado gravado pelo script (não editar)

Gravado por handoff-grava.py no momento do handoff. `--conferir` compara com o projeto agora.

- commit: 281aa811483005c5cfa8c9f3a59f459c830f0ca1 · branch: main
- arquivos sujos fora de handoffs/: 0
- `docs/analise-geral-2026-10-17.md` · sha256:c8d06f8af1a3 · citado
- `tools/hook-longrun.py` · sha256:76a68af9fbe1 · citado
- `tools/nota-retomada.py` · sha256:bfdbabd04ce7 · citado
- `tools/custo-retomada.py` · sha256:92994a68fb1e · citado
- `tests/test_hook_longrun.py` · sha256:f38f91b469c8 · citado
- `README.md` · sha256:6c11ae8667bc · citado
- `README.en.md` · sha256:02807f9c259b · citado
- `README.es.md` · sha256:b1fa3a98b65e · citado
<!-- handoff-estado:fim -->

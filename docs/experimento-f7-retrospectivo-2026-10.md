# F7 — "até onde vai": curva retrospectiva (01/10/2026)

Medição feita com `tools/medir-sessao.py --json --por-turno` sobre as três maiores sessões reais desta máquina. **Só custo e cache** — qualidade não dá para medir depois do fato; o experimento prospectivo (protocolo no fim) continua pendente.

## Resumo das sessões

| Sessão | Duração | Turnos | Compactações | Cache | Entrada total | Saída de ferramenta |
|---|---|---|---|---|---|---|
| Codex · GPT-6 Astra · JSONL de 1,84 GB | 46,7 h | 1.367 | 13 | 97,9% | 159,0 M | 916 MB (metade do arquivo) |
| Codex · GPT-5.6 Sol · 0,11 GB | 59,8 h | 951 | 6 | 97,6% | 124,0 M | 66 MB |
| Claude Code · Opus 5.5 (1M) | 17,8 h | 213 | 0 | 98,1% | 102,6 M | 23 MB |

## Curva por trecho entre compactações (Codex Astra)

| Trecho | Turnos | Entrada no fim do trecho | Cache médio |
|---|---|---|---|
| 0 (início) | 55 | 235 k | 95,1% |
| 1–5 | 61–105 | 233–240 k | 94,6–96,8% |
| 6–10 | 52–97 | 218–234 k | 93,2–96,6% |
| 11 | 180 | 192 k | 97,9% |
| 12 | 295 | 201 k | 98,3% |
| 13 (fim) | 31 | 52 k | 92,2% |

No Codex Sol, o padrão se repete: 7 trechos, de 66 a 216 turnos, com entrada final de 205–230 k e cache médio de 93,8–97,4%.

> O primeiro evento depois de cada compactação aparece com entrada 0 (é o próprio evento de compactação). Ignore esse ponto ao ler a coluna "cache mínimo".

## Claude Opus 5.5, sem compactação: a entrada por turno só cresce

| Decil da sessão | 1º | 2º | 3º | 4º | 5º | 6º | 7º | 8º | 9º | 10º |
|---|---|---|---|---|---|---|---|---|---|---|
| Entrada média/turno (k) | 157 | 244 | 297 | 398 | 447 | 493 | 581 | 657 | 716 | 810 |
| Cache | 93,7% | 98,6% | 98,8% | 99,3% | 95,0% | 99,2% | 99,3% | 99,4% | 95,2% | 99,4% |

## O que os números dizem

1. **O cache não é o motivo para cortar a sessão.** Ele fica entre 93% e 99% em todos os trechos e não piora com o número de compactações. No Codex, os trechos finais têm cache até mais alto.
2. **O Codex compacta perto de 90–93% da janela** (cerca de 230–240 k de 258 k). Isso é tarde para a qualidade do resumo (ver `pesquisa-goal-contexto-fila-2026-10.md`), e é o que o guardrail 7 do plano manda antecipar.
3. **Sem compactar, o custo por turno cresce linearmente.** No Claude com 1M de contexto, o turno do fim da sessão lê cerca de 5x mais tokens que o do início. Mesmo com cache (0,1x), cada turno no 10º decil custa por volta de 5x o do 1º.
4. **Metade do JSONL de 1,84 GB é saída de ferramenta** (916 MB), o que confirma o guardrail 5: o tamanho do log vem da saída das ferramentas.
5. **Hipótese de ponto de corte** (a validar no experimento prospectivo): no Claude com 1M, avaliar handoff quando a entrada por turno passar de cerca de 400–500 k. No Codex, compactar à mão quando a entrada passar de cerca de 150–200 k, antes do automático. A justificativa é custo por turno e risco de deterioração, não o cache.

## Protocolo do experimento prospectivo (pendente)

- **Mesma tarefa, dois modos:** (A) uma sessão contínua com `/goal`; (B) modo fila (§5.4 do plano), com cada tarefa numa sessão curta via `tools/loop-longrun.sh`.
- **Tarefa:** um backlog de 8 a 12 itens, cada um com teste congelado (nível 3), num projeto real.
- **Medir:** itens fechados com evidência, ciclos até concluir, retrabalho (itens reabertos, linhas em `failures.md`), entrada total, cache, compactações, duração. Usar `medir-sessao.py` em todas as sessões.
- **Sinais de deterioração** a contar no modo A: o mesmo plano de fechamento repetido, item feito reaberto, restrição esquecida.
- **Pronto quando:** houver tabela A × B com os números e uma recomendação de ponto de corte apoiada nela.

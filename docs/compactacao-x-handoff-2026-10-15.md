# Compactação × handoff — medição de 15/10/2026

Base: transcrições do Claude Code de 07 a 15/10/2026, Opus 5.5 (`~/.claude/projects/*/*.jsonl`).

## 1. Quando o Claude Code compacta

| Tipo | Quando | Fonte |
|---|---|---|
| Por tamanho | ~967 mil tokens nos modelos de 1M (`autoCompactWindow` / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` mudam) | doc settings-reference |
| Por ociosidade | ~55 min sem resposta, só acima de ~200 mil | registros: as 93 compactações (200–575 mil) vieram 53–58 min depois da última resposta, 85 com o resumo "você estava ausente" |

Nenhuma sessão compactou por tamanho no período. O teto de 225 mil do hook 1.2.x vinha de ler as compactações por ociosidade como limite de tamanho.

## 2. O que cada um guarda (17 compactações com handoff da mesma sessão nas 3 h antes)

| | Handoff | Resumo da compactação |
|---|---|---|
| Tamanho | 0,2–6,4 mil caracteres | 6,5–18 mil caracteres (mediana 12,3 mil) + mensagens recentes preservadas |
| Arquivos citados | 1–27 | 20–54 |
| Arquivos só nele | 0–8 por caso | 11–53 por caso |
| Separa confirmado × não verificado | sim (`[confirmed]` / `[unverified]`) | não |
| Decisões e restrições do usuário | seção própria | misturadas na narrativa |
| Próxima ação exata | seção própria | "Current/Next" quando o modelo lembra |
| Sobrevive a `/clear`, outra sessão, Codex | sim | não |

Leituras nos primeiros 25 passos: depois de compactar 51–59%; sessão nova com `/prime` 80% (13 sessões). A sessão nova redescobre mais.

## 3. Conclusão

- **Dentro da mesma sessão, a compactação preserva mais detalhe concreto** (arquivos, passos, comandos) do que o handoff. A intuição "compactar faz pior que o handoff" não se confirma em quantidade de informação.
- **O handoff ganha em qualidade e portabilidade:** separa o que foi provado do que é palpite, guarda as decisões do Nei e a próxima ação, e é o único que serve para outra sessão ou outro executor.
- **Os dois juntos são melhores que qualquer um sozinho.** O ruim é gravar o handoff a partir do resumo (cópia de cópia) ou trocar a sessão por `/clear` cedo (a sessão nova lê 80% do tempo).

## 4. Parâmetros aplicados (hook-longrun 1.3.1 → 1.4.1)

| Parâmetro | Antes | Agora | Por quê |
|---|---|---|---|
| Ponto de compactação (base das faixas) | 225 mil | ~967 mil (doc) | as faixas disparavam com 157/191 mil, no meio do trabalho |
| Faixas 50/70/85% | 112/157/191 mil | ~484/677/822 mil | — |
| Handoff contínuo (Stop, a cada 30 min) | ≥ 150 mil | ≥ 200 mil | piso da compactação por ociosidade: garante handoff antes dela |
| Depois de compactar | gravar handoff a partir do resumo | reler o handoff recente da sessão junto com o resumo; só gravar se não houver nos últimos 30 min | evita cópia de cópia e devolve as decisões que o resumo dilui |
| Faixa 3, 3ª compactação | parar e pedir sessão nova | continuar a tarefa; sessão nova só ao fim | sessão nova custa mais leitura |
| Cache vencido (60 min, ≥ 150 mil) | mantido | mantido | só pega a faixa 150–200 mil, que não compacta por ociosidade |

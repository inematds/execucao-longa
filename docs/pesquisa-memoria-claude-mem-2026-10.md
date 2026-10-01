# Memória entre sessões: o claude-mem serve? E qual banco usar para buscar no histórico

Verificação feita em 01/10/2026 nesta máquina, **só leitura**: nada foi alterado no claude-mem nem no sistema, a pedido do usuário. Complementa `pesquisa-goal-contexto-fila-2026-10.md` §5 (ideia do "RECALL").

## 1. Estado do claude-mem (v12.7.2)

**Funciona**
- O worker está de pé (`localhost:37700/api/health` → `status: ok`), com captura ao vivo: as observações desta própria sessão apareceram no banco em minutos.
- A busca responde: `api/search?query=loop-longrun` devolveu os registros do dia.
- O servidor MCP (`scripts/mcp-server.cjs`) responde a `initialize` e `tools/list` quando testado à parte. A falha "Connection closed" no início da sessão foi passageira.
- Volume: 61.890 observações, 18.746 resumos de sessão e 21.893 prompts, de maio a outubro/2026, em vários projetos (mkivideos, wifi, inemaccbot, inemapro-mono…). Esse histórico sobreviveu à limpeza de 30 dias do Claude Code.

**Problemas**
| Achado | Número | Efeito |
|---|---|---|
| Mensagens na fila nunca processadas | 7.907 (26/05 → 25/09) | buracos no histórico |
| Sessões presas como "ativas" | 3.860 de 12.311 | sessões sem resumo final |
| Fonte | 100% `claude` | sessões do Codex (5,2 GB) ficam de fora |
| Conteúdo | resumos gerados pelo Haiku | não guarda o que foi dito; cada sessão gasta cota |
| Espaço | Chroma 3,2 GB · logs 640 MB (147 arquivos, sem rotação) · SQLite 627 MB | cresce sem limite |
| Ritmo | 17–18 mil obs/mês em jul–ago → 8,6 mil em set | pode ser menos uso ou perda; merece checagem |
| Aviso antigo | `~/.claude-mem/CAPTURE_BROKEN` de 06/05 (stdin vazio, issue #2188) | provavelmente já superado, arquivo nunca foi removido |

## 2. Serve para os projetos?

- **Serve** para o agente lembrar o que já foi feito e decidido num projeto ("já resolvemos isso?", "como fizemos X?"). É memória semântica resumida, só do Claude Code.
- **Não serve** para achar palavra por palavra o que foi dito, para nada do Codex, nem para medir sessões (isso é o `tools/medir-sessao.py`).

## 3. Sugestão de banco: duas camadas

1. **claude-mem continua como memória do Claude**, com uma faxina quando o usuário decidir: reprocessar ou descartar a fila pendente, fechar sessões presas, rotacionar logs. Sempre com backup antes.
2. **Índice próprio das transcrições cruas em SQLite FTS5** (o "recall"):
   - um arquivo, sem servidor, Python da biblioteca padrão (FTS5 testado nesta máquina: SQLite 3.45.1);
   - fontes: JSONL do Codex (`~/.codex/sessions`) e do Claude Code (`~/.claude/projects`), incremental por arquivo;
   - indexa o texto do usuário, as respostas e o nome das ferramentas; **deixa de fora a saída das ferramentas** (metade do volume, quase só ruído);
   - uso: `recall "termo" [--projeto X] [--fonte codex|claude] [--desde AAAA-MM-DD]` → trecho, data, projeto e caminho da sessão;
   - o índice continua valendo depois que `tools/arquivar-sessoes.py` comprime as sessões antigas.

**Por que não outras opções**
| Opção | Motivo |
|---|---|
| Postgres + pgvector, Meilisearch, Typesense | precisam de servidor rodando; exagero para uso pessoal |
| DuckDB | ótimo para análise (curvas da F7), busca de texto mais fraca |
| Chroma | já existe dentro do claude-mem; busca por significado só depois, se a busca por palavra não bastar (dá para somar `sqlite-vec` no mesmo arquivo) |

## 4. Status

- **F9 aplicada em 01/10/2026** com `tools/faxina-claude-mem.py --aplicar`, depois de testada numa cópia do banco:
  - backup consistente antes (`~/.claude-mem/backups/claude-mem-20261001-204458-pre-faxina.db`, 657 MB, `quick_check` ok);
  - **7.904 pendências** com mais de 30 dias removidas e **3.860 sessões** presas marcadas como concluídas. Eram o mesmo conjunto: ~3.850 sessões de lotes automáticos de julho (`yt-pub-lives*`, `inemaclubpromover`, `mkivideos`) que nunca foram resumidas. **Não foram reprocessadas** (custaria ~120 MB de texto pelo Haiku, para memória de baixo valor);
  - 132 logs comprimidos: de 640 MB para 129 MB;
  - aviso `CAPTURE_BROKEN` (maio) movido para `backups/`;
  - depois: integridade ok, 61.910 observações intactas, busca respondendo e captura funcionando (a própria faxina virou observação).
  - Para desfazer: parar o worker, copiar o backup de volta e descomprimir os logs.
- **F8 feita em 01/10/2026** por execução longa (`longrun/2026-10-01-recall/`, 1 ciclo de 5 min, 15 testes congelados, conferida à parte): `tools/recall.py`, comando `recall` no PATH, timer de hora em hora. Índice real: 7.219 sessões, 90 mil trechos, 338 MB; indexação inicial 1 min 24 s, incremental 0,2 s, busca 0,02–0,04 s. As sessões internas do claude-mem (`claude-mem-observer`) ficam de fora por serem resumo do resumo.

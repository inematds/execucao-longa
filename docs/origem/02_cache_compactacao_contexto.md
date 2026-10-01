# Prompt Cache, Compactação e Contexto em Sessões Longas

## São três mecanismos diferentes

Sessão persistente, compactação e prompt caching não são a mesma coisa.

### 1. Sessão persistente

Mantém continuidade lógica do trabalho.

Permite que o agente continue operando dentro do mesmo objetivo, reutilizando o histórico e o estado disponível.

### 2. Compactação

Reduz o peso do histórico antigo.

Em vez de manter cada turno integralmente no contexto ativo, partes anteriores podem ser substituídas por uma representação condensada.

A compactação tenta preservar:

- decisões;
- requisitos;
- estado atual;
- informações importantes;
- resultados anteriores.

### 3. Prompt caching

Evita recalcular repetidamente partes idênticas do contexto.

Quando o início do prompt/contexto permanece igual, parte do processamento pode ser reutilizada.

Isso pode reduzir:

- custo;
- latência;
- computação necessária.

## Importante

Um arquivo JSONL com 1,4 GB não significa que 1,4 GB são enviados ao modelo a cada turno.

O fluxo conceitual é:

**JSONL completo**
→ histórico físico

**Sessão**
→ continuidade lógica

**Compactação**
→ representação resumida de partes antigas

**Prompt cache**
→ reaproveitamento de prefixos já processados

**Contexto ativo**
→ conteúdo efetivamente utilizado na inferência atual

## Sobre manter o cache ativo

Uma mensagem pequena pode gerar uma nova inferência e reutilizar partes do prefixo cacheável.

Mas não é correto pensar simplesmente em:

> "manter toda a sessão carregada na GPU"

A melhor forma de entender é:

> determinadas partes reutilizáveis do contexto podem continuar disponíveis para reaproveitamento por algum período.

## Compactação x cache

Existe uma relação interessante:

- antes da compactação, um prefixo grande pode ter alto reaproveitamento;
- depois da compactação, o prefixo muda;
- isso pode reduzir temporariamente o cache hit;
- em compensação, o contexto total pode ficar muito menor.

Portanto, o objetivo não é:

- nunca compactar;
- nem compactar o máximo possível.

O objetivo é encontrar o equilíbrio entre:

**CONTEXTO ÚTIL × CACHE × COMPACTAÇÃO × CUSTO × QUALIDADE**

## Métricas interessantes

Para estudar sessões longas, acompanhar:

- turno;
- input_tokens;
- cached_tokens;
- cache_write_tokens;
- output_tokens;
- número de compactações;
- tamanho do JSONL;
- latência;
- custo por turno;
- erros;
- retrabalho;
- recuperação de informações antigas;
- qualidade dos resultados.

### Cache Ratio

Uma métrica simples:

`cached_tokens / input_tokens`

Isso permite observar a eficiência real do cache ao longo da sessão.

## Nova forma de pensar o agente

Em vez de:

**CHAT → PERGUNTA → RESPOSTA**

pensar como:

**OBJETIVO → ESTADO → EXECUÇÃO → FERRAMENTAS → TESTE → COMPACTAÇÃO → CONTINUIDADE**

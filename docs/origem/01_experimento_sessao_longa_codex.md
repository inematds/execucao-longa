# Experimento de Sessão Longa no Codex

## Dados da sessão

- Tamanho do arquivo JSONL: **1.326.805 KB (~1,3 GB)**
- Registros JSONL: **55.519**
- Número de turnos: **573**
- Duração da sessão: **11 dias, 6 horas e 6 minutos**
- Sessão única com compactação
- Log completo da execução preservado

## Ideia do experimento

O objetivo é descobrir até onde uma sessão contínua do Codex pode ir mantendo:

- contexto;
- qualidade;
- custo aceitável;
- continuidade operacional;
- uso de cache;
- compactação;
- capacidade de retomar o trabalho.

A pergunta principal não é apenas se sessões longas funcionam.

A pergunta mais importante é:

> Em que ponto uma sessão longa deixa de ganhar com continuidade e começa a perder qualidade, latência ou eficiência?

## Hipótese

Sessões muito longas podem ser úteis quando o trabalho continua sendo a mesma unidade coerente de execução.

O histórico físico pode crescer muito, mas isso não significa que todo o conteúdo esteja sendo enviado integralmente ao modelo a cada turno.

O sistema pode trabalhar em diferentes camadas:

1. Histórico completo em JSONL.
2. Estado lógico da sessão.
3. Contexto ativo.
4. Compactação de histórico antigo.
5. Prompt caching.
6. Arquivos externos de estado.

## Conclusão inicial

Sessões de longa duração são possíveis.

Mas a resposta para "faz sentido?" continua sendo:

**DEPENDE.**

Faz sentido quando:

- o objetivo continua sendo o mesmo;
- o contexto acumulado ainda é relevante;
- a compactação preserva a informação essencial;
- o custo continua eficiente;
- a qualidade não degrada;
- o agente mantém um estado externo confiável.

Não faz sentido manter a mesma sessão quando o trabalho muda completamente de objetivo ou passa a exigir outro contexto.

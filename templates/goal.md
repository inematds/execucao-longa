# Goal — <slug>

- **Início:** AAAA-MM-DD HH:MM · **Agente:** Codex `/goal` | Claude `/goal` | codex exec
- **Tetos:** tempo ___ h · tokens ___ · memória ___ G

## Resultado
<o que existe quando terminar, em uma frase>

## Critérios de pronto (verificáveis)
Formato: `<comando> → <saída esperada>`. Mínimo **nível 3** (ver escala abaixo). Cubra as três camadas:

**Função** — faz o que devia
- [ ] <comando> → <saída esperada>

**Regressão** — não quebrou o que já funcionava
- [ ] <comando> → <saída esperada>

**Limite** — não mexeu onde não devia, não gastou o que não devia
- [ ] <ex.: `git diff --stat main -- tests/` → vazio>

**Teste rápido por ciclo** (segundos/minutos): <comando>
**Teste completo no final**: <comando>

<!--
ESCALA (apagar ao preencher)
  0 vago ......... "deixar bom", "melhorar"                    → reescrever
  1 subjetivo .... "revisado e limpo" (o agente se autoaprova)  → reescrever
  2 burlável ..... "0 falhas", "20 páginas" (apaga teste, página vazia) → pôr trava
  3 protegido .... comando + trava (contagem mínima, arquivo congelado/hash, validador do conteúdo) → mínimo aceito
  4 independente . nível 3 + checagem externa (e2e real, avaliador separado, amostra humana) → quando o erro custa caro

5 PERGUNTAS — cada "não" derruba o nível
  1. Dá para checar com um comando?
  2. A resposta é sim/não (sem "melhorou")?
  3. É impossível cumprir sem fazer o trabalho?
  4. A prova aparece na saída? (o avaliador do /goal no Claude só lê a conversa)
  5. Função + regressão + limite estão cobertos?

SINAIS DE CRITÉRIO RUIM: "bom/limpo/adequado/completo"; depende do agente dizer que terminou;
só contagem sem checar conteúdo; não diz o que NÃO pode mudar; verificação leva horas.
-->

## Restrições
- só pela assinatura (sem API sem autorização)
- não mexer em: <...>

## Portões humanos (parar e perguntar)
- gasto de crédito / API / render pago
- push em produção/portal, e-mail, apagar dados
- decisão de negócio ou conflito entre requisitos

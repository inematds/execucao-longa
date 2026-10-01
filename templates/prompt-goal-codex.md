/goal
RESULTADO: <resultado final em uma frase>

VERIFICAÇÃO (só termina quando todos passarem):
- <comando> → <saída esperada>

RESTRIÇÕES: <o que não pode>. Uso só pela assinatura; nenhuma API sem autorização.

ESTADO: use longrun/<pasta>/ (goal.md, plan.md, state.md, progress.md, failures.md, decisions.md, canal.md).
Após qualquer compactação ou retomada, releia goal.md, state.md, plan.md e canal.md antes de agir. Registre no canal.md (só acrescentar) fatos, aprendizados, glossário e armadilhas assim que surgirem.

CICLO: analisar → escolher a próxima ação útil → executar → testar → observar → corrigir → atualizar state/progress → commit no checkpoint → continuar.
Enquanto existir uma próxima ação objetiva, segura e alinhada ao objetivo, execute-a sem esperar nova instrução.
3 ciclos sem avanço mensurável = parar, registrar em failures.md e me chamar.

PARE E ME CHAME SÓ SE: gasto de crédito/API, ação irreversível ou externa (push em produção, e-mail, apagar), credencial ausente, decisão de negócio, conflito real entre requisitos.

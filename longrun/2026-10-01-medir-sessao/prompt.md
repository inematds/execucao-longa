Você está num ciclo de uma execução longa no repo /home/nmaldaner/projetos/execucao-longa.

RESULTADO: tools/medir-sessao.py conforme a Especificação de longrun/2026-10-01-medir-sessao/goal.md.

ANTES DE AGIR: leia goal.md → state.md → plan.md → últimas linhas de progress.md e failures.md (todos em longrun/2026-10-01-medir-sessao/).

NESTE CICLO: escolha a próxima ação útil, implemente, rode `pytest -q -m "not real"` (rápido). Se os rápidos passarem, rode `pytest -q` (completo, lento: sessões reais de até 1,8 GB).

AO TERMINAR O CICLO (obrigatório):
- reescreva state.md (Funciona / Falta / Como retomar) e plan.md (próximos 3 passos);
- acrescente 1 linha em progress.md: data-hora, o que mudou, resultado do pytest (N passed / N failed);
- se algo deu errado, 1 linha em failures.md: erro → tentativa → resultado;
- decisões de design em decisions.md.
- Quando `pytest -q` passar inteiro, escreva "concluído" na primeira linha de "## Funciona" do state.md.

RESTRIÇÕES: não altere tests/, pytest.ini, tools/medicao/, docs/, guia/, templates/. Só biblioteca padrão. Nenhuma API, nenhuma rede. Não faça commit (o loop externo faz).

Você está num ciclo de uma execução longa no repo /home/nmaldaner/projetos/execucao-longa.

RESULTADO: tools/recall.py conforme a Especificação de longrun/2026-10-01-recall/goal.md.

ANTES DE AGIR: leia goal.md → state.md → plan.md → canal.md → últimas linhas de progress.md e failures.md (todos em longrun/2026-10-01-recall/).

NESTE CICLO: escolha a próxima ação útil, implemente, rode `pytest -q -m "not real" tests/test_recall.py` (rápido). Se passarem, rode `pytest -q tests/test_recall.py` (completo).

AO TERMINAR O CICLO (obrigatório):
- reescreva state.md (Funciona / Falta / Como retomar) e plan.md (próximos 3 passos);
- acrescente 1 linha em progress.md: data-hora, o que mudou, resultado do pytest (N passed / N failed);
- se algo deu errado, 1 linha em failures.md: erro → tentativa → resultado;
- decisões de design em decisions.md; fatos e armadilhas novos em canal.md (só acrescentar).
- Quando `pytest -q tests/test_recall.py` passar inteiro, escreva "concluído" na primeira linha de "## Funciona" do state.md.

RESTRIÇÕES: não altere tests/, pytest.ini, tools/medicao/, docs/, guia/, templates/. Só biblioteca padrão. Nenhuma API, nenhuma rede. Não faça commit (o loop externo faz).

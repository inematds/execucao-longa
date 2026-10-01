# Plano

## Estratégia atual
Implementação concluída e validada nos testes congelados, incluindo sessões reais.
Preservar o escopo e deixar o versionamento para o loop externo.

## Próximos passos
1. Loop externo revisar tools/recall.py e registros deste longrun, isolando alterações de outros trabalhos.
2. Loop externo efetuar o checkpoint autorizado; este ciclo não faz commit.
3. Encerrar a execução; repetir os comandos de state.md somente se houver nova alteração.

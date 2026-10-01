# Instrução para Execução Longa no Codex

Use este modelo no início de uma tarefa longa.

```text
/goal

OBJETIVO:
[descreva exatamente o resultado final]

Trabalhe de forma contínua até atingir esse objetivo.

REGRAS:
- não pare ao terminar uma etapa;
- sempre escolha a próxima ação útil;
- execute, teste, observe, corrija e continue;
- mantenha o estado importante em arquivos;
- não dependa apenas da memória da conversa;
- atualize o progresso durante a execução;
- após compactação, releia os arquivos de estado;
- só peça minha intervenção se houver bloqueio real, credencial ausente, risco destrutivo ou decisão de negócio;
- para decisões técnicas reversíveis e seguras, decida e continue;
- valide o resultado na prática, não apenas pelo código.

Use estes arquivos:

goal.md
- objetivo final
- critérios de sucesso

plan.md
- plano atual
- próximos passos

state.md
- estado atual do projeto
- o que já funciona
- o que falta

progress.md
- etapas concluídas
- checkpoints

failures.md
- erros encontrados
- tentativas
- soluções

decisions.md
- decisões importantes
- motivos

CICLO DE TRABALHO:

ANALISAR
→ ESCOLHER PRÓXIMA AÇÃO
→ EXECUTAR
→ TESTAR
→ OBSERVAR
→ CORRIGIR
→ ATUALIZAR ESTADO
→ CONTINUAR

CONDIÇÃO DE PARADA:

Não encerre porque trabalhou muito ou terminou uma etapa.

Encerre somente quando:
1. o objetivo estiver concluído;
2. os critérios de sucesso estiverem validados;
3. não houver pendências relevantes;
4. ou existir um bloqueio real que dependa de mim.
```

## Regra principal

> Enquanto existir uma próxima ação objetiva, segura e alinhada ao objetivo, execute-a e continue sem esperar nova instrução.

## Por que isso funciona melhor

Não instrua:

> "trabalhe por 10 horas"

Prefira:

> "continue trabalhando até que esta condição verificável seja atingida"

Agentes trabalham melhor quando possuem:

- objetivo claro;
- condição de sucesso;
- autonomia delimitada;
- critérios de parada;
- estado persistente;
- ciclo de validação.

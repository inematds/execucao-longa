# Long Run Mode para AGENTS.md

Trecho recomendado para adicionar ao `AGENTS.md`.

```text
LONG-RUN MODE

Para objetivos de longa duração:
- mantenha estado persistente em arquivos;
- não pare entre subtarefas;
- retome pelo state.md após compactações;
- teste cada mudança relevante;
- continue automaticamente enquanto houver trabalho útil;
- só escale ao humano quando houver bloqueio real.
```

## Estrutura recomendada de arquivos

```text
goal.md
plan.md
state.md
progress.md
failures.md
decisions.md
```

### goal.md

Contém:

- objetivo final;
- critérios de sucesso;
- restrições principais.

### plan.md

Contém:

- estratégia atual;
- etapas;
- próximos passos.

### state.md

Contém:

- estado atual;
- componentes funcionando;
- pendências;
- contexto operacional necessário para retomar.

### progress.md

Contém:

- checkpoints;
- tarefas concluídas;
- marcos atingidos.

### failures.md

Contém:

- erros encontrados;
- tentativas;
- hipóteses;
- soluções.

### decisions.md

Contém:

- decisões importantes;
- motivos;
- trade-offs.

# Exemplo curto de /goal

```text
/goal

Transforme este sistema em uma versão pronta para produção.

Critérios:
- build funcionando;
- testes passando;
- principais bugs corrigidos;
- documentação atualizada;
- deploy validado.

Entre em modo de execução longa e continue até concluir.

Enquanto existir uma próxima ação objetiva, segura e alinhada ao objetivo, execute-a sem esperar nova instrução.

Mantenha o estado nos arquivos:
goal.md
plan.md
state.md
progress.md
failures.md
decisions.md

Após qualquer compactação, releia os arquivos de estado antes de continuar.

Só interrompa a execução quando:
- o objetivo estiver comprovadamente concluído;
- houver bloqueio real;
- faltar credencial;
- existir risco destrutivo;
- ou uma decisão de negócio depender de intervenção humana.
```

# Fluxo operacional

```text
GOAL
  ↓
PLAN
  ↓
EXECUTE
  ↓
TEST
  ↓
OBSERVE
  ↓
CORRECT
  ↓
SAVE STATE
  ↓
CONTINUE
  ↺
```

A ideia central é transformar a sessão de agente em um processo contínuo orientado por objetivo, e não em uma sequência tradicional de perguntas e respostas.

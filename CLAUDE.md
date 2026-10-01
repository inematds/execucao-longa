# CLAUDE.md — execucao-longa

Repo de documentação/plano sobre execuções longas de agentes. Conta GitHub: `inematds` (autor `inematds <inematds@gmail.com>`).

- Plano vivo: `docs/PLANO-EXECUCAO-LONGA.md`. Pesquisas datadas em `docs/pesquisa-*-AAAA-MM.md` (não reescrever as antigas; criar nova).
- Material original em `docs/origem/` — não editar.

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons
- Antes de contestar um número (TTL, preço, multiplicador), conferir primeiro as pesquisas do próprio repo em `docs/` — não opinar de memória.
- Nunca `open(f,'w')` e `open(f)` na mesma expressão (trunca antes de ler); ler para variável, depois escrever — principalmente em arquivo com mudança de outra sessão.
- Comando ad hoc segue os guardrails do plano: `codex exec` sempre com `< /dev/null` ou prompt por arquivo; nunca `pkill -f <padrão>` no mesmo comando que contém o padrão.

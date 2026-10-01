# Ejecución Larga

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Ejecución Larga](guia/assets/banner-es.jpg)](https://inematds.github.io/execucao-longa/guia/es/)

Kit para mantener a un agente (Codex `/goal` o Claude Code `/goal`) trabajando durante horas **sin perder el rumbo**: objetivo con prueba de listo, estado en archivos y reglas de parada.

📖 Guía visual: **https://inematds.github.io/execucao-longa/guia/es/**

## En 5 pasos

**1. Crea la carpeta de la ejecución en tu proyecto**
```bash
~/projetos/execucao-longa/tools/novo-longrun.sh ~/projetos/mi-proyecto mi-objetivo
# → mi-proyecto/longrun/2026-10-01-mi-objetivo/ con goal, plan, state, progress, failures, decisions
```

**2. Completa el `goal.md`** — el resultado en una frase + criterios con el formato `comando → salida esperada`, cubriendo:
- **función** (hace lo que debía) · **regresión** (no rompió el resto) · **límite** (no tocó lo que no debía)
- mínimo **nivel 3**: no se puede cumplir con un atajo (ej.: "0 fallos **y** ≥ 48 tests **y** `tests/` intacto", no solo "0 fallos")

**3. Inicia el goal**
- Codex: `codex` → pega `templates/prompt-goal-codex.md` completado en `/goal`
- Claude Code: `/goal` con `templates/prompt-goal-claude.md` — la prueba tiene que **aparecer en la salida** (el evaluador solo lee la conversación)

**4. Sigue sin interrumpir** — `/goals`, `/goal pause|resume`, `/side` (Codex). Detente e interviene si:
- 3 ciclos sin avance medible;
- el agente repite "voy a terminar y hacer commit" sin terminar, o reabre ítems ya hechos (el contexto se degradó);
- 3.ª compactación en la misma sesión → handoff + sesión nueva.

**5. Cierra y mide** — `state.md` dice "concluido", los criterios pasan, y:
```bash
python3 ~/projetos/execucao-longa/tools/medicao/cx.py   # Codex: duración, compactaciones, tokens, caché
python3 ~/projetos/execucao-longa/tools/medicao/cc.py   # Claude Code: cache_read %, duración
```

## Úsalo cuando / no lo uses cuando

| ✅ Úsalo | ❌ No lo uses (o divide en sesiones más cortas) |
|---|---|
| Un objetivo, comprobable con un comando | El objetivo cambia a mitad de camino |
| Trabajo local y reversible | Pasos pagos/irreversibles en el camino (pasan a ser puertas humanas) |
| Se puede medir el avance en cada ciclo | No hay forma de verificar más allá de "parece bien" |

¿Muchas tareas pequeñas y un backlog que crece? Usa el **modo cola** (plan §5.4).

## Qué hay aquí

| | |
|---|---|
| [`tools/novo-longrun.sh`](tools/novo-longrun.sh) | Crea la carpeta `longrun/` de una ejecución a partir de las plantillas |
| [`templates/`](templates/) | `goal.md` (con la escala de criterios), `state/plan/progress/failures/decisions.md`, prompts `/goal` y el fragmento LONG-RUN para `AGENTS.md`/`CLAUDE.md` |
| [`tools/medicao/`](tools/medicao/) | Scripts que leen los JSONL de sesión (Codex y Claude Code): duración, compactaciones, tokens, caché |
| [Plan](docs/PLANO-EXECUCAO-LONGA.md) | El método completo: criterios (§3.1), archivos de estado, recetas por herramienta, modo cola, guardrails, fases (en portugués) |
| [Investigación jul–oct/2026](docs/pesquisa-web-2026-10.md) | Qué cambió en Codex, Claude Code y otros, con fuentes (en portugués) |
| [Investigación: `/goal`, contexto y cola](docs/pesquisa-goal-contexto-fila-2026-10.md) | Deterioro de contexto, caché entre ciclos, modo cola (Symphony/Linear) (en portugués) |
| [`docs/origem/`](docs/origem/) | Material que originó el proyecto |

Estado: F0 (método, plantillas y scripts). Próximas fases en el §8 del plan.

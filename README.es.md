# Ejecución Larga

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Ejecución Larga](guia/assets/banner-es.jpg)](https://inematds.github.io/execucao-longa/guia/es/)

Kit para mantener a un agente (Codex `/goal` o Claude Code `/goal`) trabajando durante horas **sin perder el rumbo**: objetivo con prueba de listo, estado en archivos y reglas de parada.

📖 Guía visual: **https://inematds.github.io/execucao-longa/guia/es/**

## En 5 pasos

**1. Crea la carpeta de la ejecución en tu proyecto**
```bash
~/projetos/execucao-longa/tools/novo-longrun.sh ~/projetos/mi-proyecto mi-objetivo
# → mi-proyecto/longrun/2026-10-01-mi-objetivo/ con goal, plan, state, progress, failures, decisions y canal (notas de lo que la compactación pierde)
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

**5. Cierra y mide** — `state.md` dice "concluido", corres el test final por tu cuenta, y:
```bash
python3 ~/projetos/execucao-longa/tools/medir-sessao.py <sesión.jsonl>             # duración, compactaciones, tokens, caché
python3 ~/projetos/execucao-longa/tools/medir-sessao.py <sesión.jsonl> --json --por-turno
```

**¿Prefieres que corra solo?** En lugar del paso 3, pon `prompt.md` + `loop.env` en la carpeta (copia de [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/)) y corre `tools/loop-longrun.sh <carpeta>`. Cada ciclo es un `codex exec` con tope; el test decide si sigue, y el loop se detiene solo (concluido, estancamiento o tope).

## Instalar una vez por máquina

1. Clona en `~/projetos/execucao-longa`.
2. Pega [`templates/AGENTS-long-run.md`](templates/AGENTS-long-run.md) en el `CLAUDE.md` y el `AGENTS.md` globales — el agente sigue el método sin que se lo recuerden.
3. Instala las skills `session-handoff` y `prime` de **[skillmanager3x](https://inematds.github.io/skillmanager3x/guia/es/)** ([repo](https://github.com/inematds/skillmanager3x); misma versión del kit [agente-claude-codex](https://github.com/inematds/agente-claude-codex) 1.5.2): `cp -r skill/pt/session-handoff skill/pt/prime ~/.claude/skills/`. El hook solo **pide** el handoff; quienes lo graban (`handoff-grava.py`, `latest.md` como índice de abiertos) y lo retoman (`/prime`) son esas skills. Desde la 1.5.2 el handoff se verifica: el script graba el commit y el sha256 de los archivos (`handoff-grava.py --conferir` detecta un handoff viejo), cada `[confirmed]` apunta a un commit, prueba o archivo, y 5 preguntas de prueba permiten que `/prime` muestre cuánto recuperó (N/5).
4. En `~/.claude/settings.json`, conecta `tools/hook-longrun.sh` a `PreCompact`, `SessionStart` (matcher `compact|resume|clear`), `PostToolUse`, `UserPromptSubmit` y `Stop`. Avisa al agente por **franja de contexto**, medida sobre el **punto en que Claude Code compacta** (~967 mil en los modelos de 1M, según la documentación de Claude Code; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` o `LONGRUN_TETO` lo cambian. Las compactaciones de 200–575 mil vistas en los registros eran por **inactividad**, ~55 min sin actividad, no por tamaño): ~50% → anotar en `canal.md`; ~70% → actualizar el estado y `/compact`; ~85% → `/session-handoff` + sesión nueva + `/prime`. También pide releer el estado tras compactar o retomar. En cualquier sesión pide el handoff en ~70%/~85% y tras compactar, **comprueba** en la transcripción que se grabó un archivo en `handoffs/history/` (insiste hasta 2 veces y avisa "handoff verificado" o "NO se grabó"), pide sesión nueva en la 3.ª compactación y, tras más de 60 min parado con contexto de más de 150 mil, **bloquea una vez** el mensaje para avisar que el caché venció (reenviar continúa; `/clear` empieza limpio y la sesión nueva señala el último handoff). Y pon `"cleanupPeriodDays": 365` (el valor por defecto de 30 días borra las transcripciones). **Handoff por inactividad (1.5.1, evento `Stop`):** al terminar cada respuesta, con contexto ≥ 200 mil tokens y la carpeta `handoffs/`, el hook solo **programa** (timer `systemd-run --user`, uno por sesión, rehecho en cada respuesta) una revisión para dentro de 30 min. Si la sesión sigue parada, sin handoff reciente y con la caché de 1 h vigente (< 55 min), graba el handoff en una **copia** de la sesión (`claude -p --resume --fork-session`, mismo modelo, caché caliente) que solo puede ejecutar `handoff-grava.py` y leer archivos; registro en `~/.local/state/execucao-longa/ocioso.log`, y el aviso de caché vencida menciona el handoff grabado. Ya no se interrumpe a quien está trabajando: el pedido "Handoff continuo" de la 1.1–1.4 (cada 30 min de trabajo) queda apagado (`LONGRUN_CONTINUO_TOKENS=200000` lo vuelve a encender). Ajustes: `LONGRUN_OCIOSO_MIN`, `LONGRUN_OCIOSO_TOKENS` (0 lo apaga), `LONGRUN_CACHE_MIN`. **Índice de abiertos (1.2.0):** con el `latest.md` en formato índice (grabado por el `handoff-grava.py` de la skill session-handoff, kit agente-claude-codex 1.4.1+, distribuida también por skillmanager3x), la sesión limpia lista todos los trabajos abiertos del proyecto, no solo el último, y avisa los snapshots cuyo sello en el nombre es posterior a la grabación (sello inventado).
5. Vigía: copia `tools/systemd/longrun-vigia.*` a `~/.config/systemd/user/` y corre `systemctl --user enable --now longrun-vigia.timer` (avisa ejecuciones detenidas u ociosas).
6. Crons que llaman agentes: `flock -n <lock> timeout <tope> <script>`.

## "Sessão parada há Xh: o cache venceu" (sesión detenida, caché vencido) no es un error

Al volver a una sesión detenida hace más de 60 min con más de 150 mil tokens de contexto, el hook (`UserPromptSubmit`, función `pausa` en `tools/hook-longrun.py`) **retiene el primer mensaje una vez**. El caché del prompt dura ~1 h; después, el siguiente mensaje relee toda la conversación sin caché y gasta mucho del límite. El aviso te deja elegir antes de pagar.

Ejemplo real (sesión detenida hace 5h33 con 220 mil tokens; el aviso del hook está en portugués):

```
● UserPromptSubmit operation blocked by hook:
  Sessão parada há 5h33: o cache venceu e esta mensagem vai reprocessar ~220 mil tokens do seu limite.
  Para continuar aqui, reenvie a mensagem. Para começar limpo: /clear e depois /prime
  (o último handoff do projeto é indicado na abertura).

  Original prompt: ficou muito ruim, a movimentação da apresentação...
```

Qué hacer:

- **Seguir en esta sesión:** reenvía el mismo mensaje. Pasa directo (la retención vale una vez por pausa y queda guardada en el estado de la sesión).
- **Empezar liviano (recomendado):** `/clear` y luego `/prime`. La sesión nueva lee el último handoff y repites el pedido con ~20 mil tokens en lugar de 220 mil.

Cada sesión cuenta aparte: dos sesiones detenidas muestran el aviso una vez cada una. Ajuste por variable de entorno:

| Variable | Por defecto | Efecto |
|---|---|---|
| `LONGRUN_PAUSA_MIN` | `60` | minutos detenido antes de retener (ej.: `120`) |
| `LONGRUN_PAUSA_TOKENS` | `150000` | contexto mínimo para retener; `0` lo desactiva |

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
| [`tools/loop-longrun.sh`](tools/loop-longrun.sh) | Loop headless: ciclos de `codex exec` con flock, timeout y tope de memoria; el test decide; se detiene por estancamiento |
| [`tools/medir-sessao.py`](tools/medir-sessao.py) | Mide una sesión (Codex o Claude): duración, compactaciones, tokens, caché, salida de herramientas, curva por turno |
| [`tools/hook-longrun.sh`](tools/hook-longrun.sh) | Hook de Claude Code: franjas de contexto (50/70/85% del punto de compactación), handoff verificado, aviso de caché vencido, guardar antes de compactar y releer después |
| [`tools/vigia.py`](tools/vigia.py) | Vigía (timer cada 10 min): avisa ejecuciones detenidas, detenidas sin aviso u ociosas |
| [`tools/arquivar-sessoes.py`](tools/arquivar-sessoes.py) | Higiene: informe del espacio de las sesiones antiguas; `--aplicar` comprime, `--restaurar` devuelve |
| [`tools/recall.py`](tools/recall.py) | Comando `recall`: busca en todo lo dicho con Codex y Claude (índice SQLite FTS5, reindexado cada hora) |
| [`tools/faxina-claude-mem.py`](tools/faxina-claude-mem.py) | Limpieza de claude-mem con respaldo: cola antigua, sesiones trabadas, logs |
| [`templates/`](templates/) | `goal.md` (con la escala de criterios), `state/plan/progress/failures/decisions.md`, prompts `/goal` y el fragmento LONG-RUN para `AGENTS.md`/`CLAUDE.md` |
| [`longrun/2026-10-01-medir-sessao/`](longrun/2026-10-01-medir-sessao/) | Ejemplo real: el piloto que construyó `medir-sessao.py` en 1 ciclo |
| [Plan](docs/PLANO-EXECUCAO-LONGA.md) | El método completo: criterios (§3.1), archivos de estado, recetas, modo cola, guardrails, fases y lecciones del piloto (en portugués) |
| [F7 retrospectiva](docs/experimento-f7-retrospectivo-2026-10.md) | Curva de caché y costo por turno en 3 sesiones reales + protocolo del experimento (en portugués) |
| [Investigación jul–oct/2026](docs/pesquisa-web-2026-10.md) | Qué cambió en Codex, Claude Code y otros, con fuentes (en portugués) |
| [Investigación: `/goal`, contexto y cola](docs/pesquisa-goal-contexto-fila-2026-10.md) | Deterioro de contexto, caché entre ciclos, modo cola (Symphony/Linear) (en portugués) |
| [Investigación: memoria, claude-mem y base de datos](docs/pesquisa-memoria-claude-mem-2026-10.md) | ¿Funciona claude-mem? ¿Sirve para los proyectos? Índice SQLite FTS5 sugerido (recall) — propuesta F8/F9 (en portugués) |
| [`docs/origem/`](docs/origem/) | Material que originó el proyecto |

Estado: F0–F5 hechas; F6 lista (no aplicada); F7 con curva retrospectiva, experimento prospectivo pendiente. F8 (recall) y F9 (limpieza de claude-mem) hechas. Detalles en el §8 del plan.

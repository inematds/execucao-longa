#!/usr/bin/env python3
"""Hook do Claude Code para execuções longas e handoff automático.

Em QUALQUER sessão (sem longrun ativo):
  PostToolUse / UserPromptSubmit → em 70% e 85% do contexto: grave o handoff agora (skill session-handoff),
      enquanto o cache ainda está quente e ler o histórico sai barato; em 85% também sugira sessão nova.
  SessionStart (compact)        → houve compactação: grave o handoff a partir do resumo, se ainda não gravou.

Com longrun/*/state.md sem "concluído" no projeto, valem as mensagens de execução longa abaixo
(que também incluem o handoff nas faixas 2 e 3):

  PreCompact                    → systemMessage: salve state/progress/canal antes do resumo
  SessionStart (compact|resume) → additionalContext: releia goal → state → plan → canal → fim de progress/failures
  PostToolUse / UserPromptSubmit → faixas de uso do contexto (padrão 50/70/85%), uma vez por faixa por sessão:
      faixa 1: registrar conhecimento no canal.md
      faixa 2: atualizar estado e pedir /compact
      faixa 3: parar de abrir trabalho novo; /session-handoff + sessão nova + /prime
  A % é a mesma conta do statusline: último usage da transcrição ÷ janela do modelo.
  Depois de uma compactação a % cai e as faixas voltam a valer.

Ajustes por ambiente: LONGRUN_FAIXAS="50,70,85"  LONGRUN_JANELA=1000000  LONGRUN_DEBUG=<arquivo> (grava o que o hook recebe)
O Claude Code grava a transcrição com atraso: o aviso de faixa costuma chegar uma chamada de ferramenta depois.
"""
import json, os, pathlib, re, subprocess, sys

ESTADO = pathlib.Path(os.environ.get("LONGRUN_ESTADO", pathlib.Path.home() / ".local/state/execucao-longa/faixas"))


def saida(obj):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)


def ativas(cwd):
    try:
        raiz = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or cwd
    except Exception:
        raiz = cwd
    out = []
    for s in sorted(pathlib.Path(raiz).glob("longrun/*/state.md")):
        t = s.read_text(errors="ignore").lower()
        if "concluído" not in t and "concluido" not in t:
            out.append(str(s.parent.relative_to(raiz)))
    return out


def uso_contexto(transcript):
    """(tokens, janela) do último usage da transcrição; lê só o fim do arquivo."""
    try:
        tam = os.path.getsize(transcript)
    except OSError:
        return 0, 0
    for janela_leitura in (2 << 20, 32 << 20):
        with open(transcript, "rb") as f:
            f.seek(max(0, tam - janela_leitura))
            linhas = f.read().splitlines()
        for ln in reversed(linhas):
            if b'"usage"' not in ln:
                continue
            try:
                m = json.loads(ln).get("message") or {}
                u = m["usage"]
            except (ValueError, KeyError, AttributeError, TypeError):
                continue
            tok = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            modelo = (m.get("model") or "").lower()
            janela = int(os.environ.get("LONGRUN_JANELA", 0)) or (200_000 if "haiku" in modelo and tok <= 200_000 else 1_000_000)
            return tok, janela
        if tam <= janela_leitura:
            break
    return 0, 0


HANDOFF = ("grave o handoff AGORA com a skill session-handoff (handoffs/history/<UTC>.md + handoffs/latest.md), "
           "sem esperar o usuário pedir: o cache ainda está quente e ler o histórico sai barato. Depois avise em uma linha "
           "que gravou e continue o trabalho.")
HANDOFF_POS_COMPACT = ("Se nesta sessão ainda não foi gravado um handoff depois da última tarefa concluída, grave-o agora "
                       "com a skill session-handoff a partir do resumo (sem esperar pedido) e avise em uma linha.")


def subiu_faixa(d):
    """(nível novo, %, tokens, janela) quando o contexto entra numa faixa acima da última avisada; nível 0 se não."""
    tok, janela = uso_contexto(d.get("transcript_path", ""))
    if not janela:
        return 0, 0, 0, 0
    pct = 100 * tok / janela
    faixas = [int(x) for x in os.environ.get("LONGRUN_FAIXAS", "50,70,85").split(",")]
    nivel = max([i + 1 for i, f in enumerate(faixas) if pct >= f], default=0)
    ESTADO.mkdir(parents=True, exist_ok=True)
    marca = ESTADO / re.sub(r"[^A-Za-z0-9_-]", "_", d.get("session_id", "sem-id"))
    try:
        ultimo = int(marca.read_text())
    except (OSError, ValueError):
        ultimo = 0
    if nivel != ultimo:
        marca.write_text(str(nivel))  # cai depois de compactar → faixas voltam a valer
    return (nivel if nivel > ultimo else 0), pct, tok, janela


def sem_longrun(d, ev):
    """Sessão comum: handoff automático na faixa 2 (70%) e 3 (85%) e depois de compactar."""
    if ev == "SessionStart" and d.get("source") == "compact":
        saida({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": HANDOFF_POS_COMPACT}})
    if ev not in ("PostToolUse", "UserPromptSubmit"):
        return
    nivel, pct, tok, janela = subiu_faixa(d)
    if nivel < 2:
        return
    medida = f"Contexto em {pct:.0f}% ({tok // 1000} mil de {janela // 1000} mil tokens)."
    if nivel == 2:
        ctx = f"{medida} Terminada a ação em curso, " + HANDOFF
    else:
        ctx = (f"{medida} Não abra trabalho novo: " + HANDOFF.replace(" e continue o trabalho.", ".")
               + " Sugira ao usuário sessão nova + /prime.")
    saida({"hookSpecificOutput": {"hookEventName": ev, "additionalContext": ctx},
           "systemMessage": f"Contexto em {pct:.0f}%: o agente vai gravar o handoff."})


def main():
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return
    if os.environ.get("LONGRUN_DEBUG"):
        with open(os.environ["LONGRUN_DEBUG"], "a") as f:
            f.write(json.dumps(d, ensure_ascii=False)[:600] + "\n")
    ev, cwd = d.get("hook_event_name", ""), d.get("cwd", "")
    if not cwd or not os.path.isdir(cwd):
        return
    pastas = ativas(cwd)
    if not pastas:
        return sem_longrun(d, ev)
    lista = ", ".join(pastas)

    if ev == "PreCompact":
        saida({"systemMessage": f"Execução longa ativa ({lista}): a compactação vai resumir o histórico. "
                                "Garanta que state.md, progress.md e canal.md estão atualizados."})

    if ev == "SessionStart":
        extra = (" " + HANDOFF_POS_COMPACT) if d.get("source") == "compact" else ""
        saida({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
            f"EXECUÇÃO LONGA ATIVA neste projeto ({lista}). O contexto foi compactado ou a sessão foi retomada: "
            "antes de qualquer ação, releia goal.md → state.md → plan.md → canal.md e as últimas linhas de "
            "progress.md e failures.md dessa pasta, e continue do primeiro item pendente sem reabrir o que já está feito."
            + extra}})

    if ev not in ("PostToolUse", "UserPromptSubmit"):
        return
    nivel, pct, tok, janela = subiu_faixa(d)
    if not nivel:
        return

    canal = " e ".join(f"{p}/canal.md" for p in pastas)
    medida = f"Contexto em {pct:.0f}% ({tok // 1000} mil de {janela // 1000} mil tokens)."
    msgs = {
        1: (f"{medida} FAIXA 1 de 3: antes de seguir, acrescente em {canal} o que você precisaria se o histórico "
            "sumisse agora — fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas. Só acrescentar. "
            "Depois continue o trabalho normalmente.", None),
        2: (f"{medida} FAIXA 2 de 3: atualize state.md, progress.md e {canal}; termine a unidade de trabalho atual "
            "e grave o handoff agora (skill session-handoff, sem esperar pedido); depois avise o usuário que é hora de rodar /compact (compactar cedo resume melhor do que o automático perto do limite).",
            f"Execução longa em {pct:.0f}% do contexto: hora de /compact (o agente foi avisado)."),
        3: (f"{medida} FAIXA 3 de 3: não abra trabalho novo. Atualize state.md, progress.md e {canal} e peça ao usuário: "
            "/session-handoff, sessão nova e /prime (ou releitura da pasta longrun/). Sem humano por perto, siga só até o próximo checkpoint.",
            f"Execução longa em {pct:.0f}% do contexto: hora de /session-handoff + sessão nova + /prime."),
    }
    ctx, aviso = msgs[min(nivel, 3)]
    out = {"hookSpecificOutput": {"hookEventName": ev, "additionalContext": ctx}}
    if aviso:
        out["systemMessage"] = aviso
    saida(out)


if __name__ == "__main__":
    main()

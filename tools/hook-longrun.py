#!/usr/bin/env python3
"""Hook do Claude Code para execuções longas, handoff conferido e sessão parada (cache vencido).

Em QUALQUER sessão (sem longrun ativo):
  PostToolUse / UserPromptSubmit → nas faixas 2 e 3 do contexto: grave o handoff agora (skill session-handoff),
      enquanto o cache ainda está quente; na faixa 3 também sugira sessão nova.
  SessionStart (compact)        → houve compactação: grave o handoff a partir do resumo; na 3ª compactação da
      mesma sessão, peça também sessão nova (/clear + /prime).
  Conferência do handoff        → depois de cada pedido, o hook procura na transcrição uma gravação em
      handoffs/history/ feita depois do pedido e confere que o arquivo existe. Se em 8 eventos não houver,
      cobra de novo (até 2 vezes) e depois avisa o usuário que o handoff NÃO foi gravado. Ao achar, avisa
      "handoff conferido". Só vale em projeto com a pasta handoffs/.
  UserPromptSubmit após pausa   → se a última resposta foi há mais de 60 min (o cache venceu) e o contexto é
      grande, BLOQUEIA uma vez o envio e explica: reenviar continua (relendo tudo sem cache) ou /clear limpa.
  SessionStart (clear)          → aponta o último handoff do projeto para o agente ler com /prime se o pedido
      continuar aquele trabalho.
  Stop (handoff contínuo)       → ao fim de uma resposta, com contexto ≥ 150 mil tokens e nenhum handoff gravado
      por ESTA sessão nos últimos 30 min, devolve "block" uma vez: o agente atualiza o handoff com o cache quente
      (~20 mil tokens equivalentes contra 250–400 mil de releitura fria depois de parado). No máximo 1 pedido a cada
      30 min por sessão; nunca quando o próprio Stop já fez o agente continuar (stop_hook_active). Só em projeto com
      a pasta handoffs/.

Com longrun/*/state.md sem "concluído" no projeto, valem as mensagens de execução longa abaixo
(que também incluem o handoff nas faixas 2 e 3):

  PreCompact                    → systemMessage: salve state/progress/canal antes do resumo
  SessionStart (compact|resume) → additionalContext: releia goal → state → plan → canal → fim de progress/failures
  PostToolUse / UserPromptSubmit → faixas de uso do contexto (padrão 50/70/85%), uma vez por faixa por sessão:
      faixa 1: registrar conhecimento no canal.md
      faixa 2: atualizar estado e pedir /compact
      faixa 3: parar de abrir trabalho novo; /session-handoff + sessão nova + /prime

A % é calculada sobre o TETO, não sobre a janela do modelo: o Claude Code compacta o Opus 5.5 entre 200 e
575 mil tokens (mediana 254 mil, 93 compactações de 07 a 15/10/2026) mesmo com janela de 1 milhão; sobre
1 milhão as faixas de 70/85% nunca disparavam. Teto padrão 225 mil → faixas em ~112/157/191 mil.
Depois de uma compactação a % cai e as faixas voltam a valer.

Ajustes por ambiente: LONGRUN_FAIXAS="50,70,85"  LONGRUN_TETO=225000  LONGRUN_JANELA=<força a janela>
  LONGRUN_PAUSA_MIN=60  LONGRUN_PAUSA_TOKENS=150000 (0 desliga o bloqueio)  LONGRUN_DEBUG=<arquivo>
  LONGRUN_CONTINUO_TOKENS=150000 (0 desliga o handoff contínuo)  LONGRUN_CONTINUO_MIN=30
O Claude Code grava a transcrição com atraso: o aviso de faixa costuma chegar uma chamada de ferramenta depois.
"""
import datetime, json, os, pathlib, re, subprocess, sys, time

VERSAO = "1.1.0"

ESTADO = pathlib.Path(os.environ.get("LONGRUN_ESTADO", pathlib.Path.home() / ".local/state/execucao-longa/faixas"))
COBRAR_APOS = 8      # eventos sem handoff antes de cobrar de novo
MAX_COBRANCAS = 2


def env_int(nome, padrao):
    try:
        return int(os.environ.get(nome, padrao))
    except ValueError:
        return padrao


def saida(obj):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)


def raiz_de(cwd):
    try:
        return subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or cwd
    except Exception:
        return cwd


def ativas(raiz):
    out = []
    for s in sorted(pathlib.Path(raiz).glob("longrun/*/state.md")):
        t = s.read_text(errors="ignore").lower()
        if "concluído" not in t and "concluido" not in t:
            out.append(str(s.parent.relative_to(raiz)))
    return out


# ---------- estado por sessão ----------
def arq_estado(d):
    return ESTADO / re.sub(r"[^A-Za-z0-9_-]", "_", d.get("session_id", "sem-id"))


def carregar(d):
    try:
        t = arq_estado(d).read_text().strip()
    except OSError:
        return {}
    try:
        v = json.loads(t)
    except ValueError:
        return {}
    return v if isinstance(v, dict) else {"nivel": int(v)}  # formato antigo: só o número da faixa


def salvar(d, st):
    ESTADO.mkdir(parents=True, exist_ok=True)
    arq_estado(d).write_text(json.dumps(st))


# ---------- leitura da transcrição ----------
def fim_transcricao(transcript, tamanho=2 << 20):
    try:
        tam = os.path.getsize(transcript)
        with open(transcript, "rb") as f:
            f.seek(max(0, tam - tamanho))
            return f.read().splitlines(), tam <= tamanho
    except (OSError, TypeError):
        return [], True


def uso_contexto(transcript):
    """(tokens, janela efetiva) do último usage da transcrição; lê só o fim do arquivo."""
    for janela_leitura in (2 << 20, 32 << 20):
        linhas, inteiro = fim_transcricao(transcript, janela_leitura)
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
            janela = env_int("LONGRUN_JANELA", 0) or (200_000 if "haiku" in modelo and tok <= 200_000 else 1_000_000)
            return tok, min(janela, env_int("LONGRUN_TETO", 225_000) or janela)
        if inteiro:
            break
    return 0, 0


def ts_iso(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return 0.0


def ultima_resposta(transcript):
    """Hora (epoch) da última mensagem do assistente na transcrição."""
    linhas, _ = fim_transcricao(transcript)
    for ln in reversed(linhas):
        if b'"assistant"' not in ln:
            continue
        try:
            reg = json.loads(ln)
        except ValueError:
            continue
        if reg.get("type") == "assistant":
            return ts_iso(reg.get("timestamp", ""))
    return 0.0


RE_HIST = re.compile(r"handoffs/history/[A-Za-z0-9_.:+-]+\.md")


def handoff_gravado(transcript, desde, raiz):
    """Caminho do handoff gravado por ESTA sessão depois de `desde`, conferido no disco; None se não houver."""
    linhas, _ = fim_transcricao(transcript, 8 << 20)
    for ln in reversed(linhas):
        if b"handoffs/history/" not in ln or b'"tool_use"' not in ln:
            continue
        try:
            reg = json.loads(ln)
        except ValueError:
            continue
        if ts_iso(reg.get("timestamp", "")) < desde - 5:
            break
        for c in (reg.get("message") or {}).get("content") or []:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            for rel in RE_HIST.findall(json.dumps(c.get("input", {}), ensure_ascii=False)):
                p = pathlib.Path(raiz) / rel
                try:
                    if p.stat().st_size >= 200 and p.stat().st_mtime >= desde - 5:
                        return rel
                except OSError:
                    continue
    return None


def hora(epoch):
    return time.strftime("%H:%M", time.localtime(epoch))


# ---------- regras ----------
HANDOFF = ("grave o handoff AGORA com a skill session-handoff (handoffs/history/<UTC>.md + handoffs/latest.md), "
           "sem esperar o usuário pedir: o cache ainda está quente e ler o histórico sai barato. Depois avise em uma linha "
           "que gravou e continue o trabalho.")
HANDOFF_POS_COMPACT = ("Se nesta sessão ainda não foi gravado um handoff depois da última tarefa concluída, grave-o agora "
                       "com a skill session-handoff a partir do resumo (sem esperar pedido) e avise em uma linha.")


def subiu_faixa(d, st):
    """(nível novo, %, tokens, janela) quando o contexto entra numa faixa acima da última avisada; nível 0 se não."""
    tok, janela = uso_contexto(d.get("transcript_path", ""))
    if not janela:
        return 0, 0, 0, 0
    pct = 100 * tok / janela
    faixas = [int(x) for x in os.environ.get("LONGRUN_FAIXAS", "50,70,85").split(",")]
    nivel = max([i + 1 for i, f in enumerate(faixas) if pct >= f], default=0)
    ultimo = st.get("nivel", 0)
    st["nivel"] = nivel  # cai depois de compactar → faixas voltam a valer
    return (nivel if nivel > ultimo else 0), pct, tok, janela


def pedir_handoff(st, raiz):
    if (pathlib.Path(raiz) / "handoffs").is_dir():
        st.update(pedido=time.time(), eventos=0, cobrancas=0)


def conferir_handoff(d, st, raiz):
    """(additionalContext, systemMessage) da conferência de um handoff pedido antes."""
    if not st.get("pedido"):
        return None, None
    rel = handoff_gravado(d.get("transcript_path", ""), st["pedido"], raiz)
    if rel:
        st.pop("pedido", None)
        return None, f"Handoff conferido: {rel}."
    st["eventos"] = st.get("eventos", 0) + 1
    if st["eventos"] < COBRAR_APOS:
        return None, None
    st["eventos"] = 0
    if st.get("cobrancas", 0) >= MAX_COBRANCAS:
        st.pop("pedido", None)
        return None, f"Atenção: o handoff pedido às {hora(st.get('pedido_h', time.time()))} NÃO foi gravado; peça /session-handoff antes de limpar."
    st["cobrancas"] = st.get("cobrancas", 0) + 1
    st["pedido_h"] = st.get("pedido_h", st["pedido"])
    return ("O handoff pedido pelo hook às " + hora(st["pedido"]) + " AINDA NÃO FOI GRAVADO (nenhuma escrita nova em "
            "handoffs/history/ nesta sessão). Assim que terminar a ação em curso, grave-o com a skill session-handoff "
            "e avise em uma linha."), None


def pausa(d, st):
    """Bloqueia UMA vez o primeiro envio depois de uma pausa maior que o cache, se o contexto for grande."""
    if d.get("hook_event_name") != "UserPromptSubmit":
        return None
    minimo = env_int("LONGRUN_PAUSA_TOKENS", 150_000)
    if not minimo:
        return None
    t = d.get("transcript_path", "")
    ultima = ultima_resposta(t)
    parado = (time.time() - ultima) / 60 if ultima else 0
    if parado < env_int("LONGRUN_PAUSA_MIN", 60) or st.get("pausa_liberada") == ultima:
        return None
    tok, _ = uso_contexto(t)
    if tok < minimo:
        return None
    st["pausa_liberada"] = ultima  # reenviar passa
    h, m = divmod(int(parado), 60)
    return (f"Sessão parada há {h}h{m:02d}: o cache venceu e esta mensagem vai reprocessar ~{tok // 1000} mil tokens "
            "do seu limite. Para continuar aqui, reenvie a mensagem. Para começar limpo: /clear e depois /prime "
            "(o último handoff do projeto é indicado na abertura).")


def ultimo_handoff(raiz):
    hist = pathlib.Path(raiz) / "handoffs" / "history"
    try:
        arqs = sorted(hist.glob("*.md"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return None
    return arqs[-1] if arqs else None


def ao_limpar(d, raiz):
    p = ultimo_handoff(raiz)
    if not p:
        return
    saida({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
        f"Sessão limpa. Último handoff deste projeto: {p.relative_to(raiz)} (gravado em "
        f"{time.strftime('%d/%m %H:%M', time.localtime(p.stat().st_mtime))}; outras sessões podem gravar no mesmo "
        "projeto). Se o primeiro pedido do usuário continuar aquele trabalho, leia-o com a skill prime antes de agir; "
        "não retome publicação, envio ou deploy por conta própria."}})


def continuo(d, st, raiz):
    """Stop: pede UMA atualização do handoff com o cache quente; None se não for hora."""
    minimo = env_int("LONGRUN_CONTINUO_TOKENS", 150_000)
    if not minimo or d.get("stop_hook_active") or not (pathlib.Path(raiz) / "handoffs").is_dir():
        return None
    intervalo = env_int("LONGRUN_CONTINUO_MIN", 30) * 60
    agora = time.time()
    if agora - st.get("continuo", 0) < intervalo:
        return None
    t = d.get("transcript_path", "")
    tok, _ = uso_contexto(t)
    if tok < minimo or handoff_gravado(t, agora - intervalo, raiz):
        return None
    st["continuo"] = agora
    pedir_handoff(st, raiz)  # a conferência confirma nos próximos eventos
    return (f"Handoff contínuo: contexto em {tok // 1000} mil tokens e nenhum handoff desta sessão nos últimos "
            f"{intervalo // 60} min. Antes de parar, atualize o handoff com a skill session-handoff "
            "(handoffs/history/<UTC>.md + handoffs/latest.md): com o cache quente sai barato. Não comece trabalho novo; "
            "termine com uma linha \"Handoff atualizado: <arquivo>\".")


def emitir(ev, ctx=None, aviso=None):
    out = {}
    if ctx:
        out["hookSpecificOutput"] = {"hookEventName": ev, "additionalContext": ctx}
    if aviso:
        out["systemMessage"] = aviso
    if out:
        saida(out)


def pos_compact(st, raiz, extra_base):
    st["compactacoes"] = st.get("compactacoes", 0) + 1
    st["nivel"] = 0
    pedir_handoff(st, raiz)
    n = st["compactacoes"]
    if n >= 3:
        return (extra_base + f" Esta é a {n}ª compactação desta sessão: depois do handoff, peça ao usuário sessão nova "
                "(/clear + /prime), porque cada resumo perde detalhe."), f"{n}ª compactação: hora de handoff + /clear + /prime."
    return extra_base, None


def sem_longrun(d, ev, st, raiz):
    """Sessão comum: handoff nas faixas 2 e 3 e depois de compactar, com conferência."""
    if ev == "SessionStart":
        if d.get("source") == "compact":
            ctx, aviso = pos_compact(st, raiz, HANDOFF_POS_COMPACT)
            salvar(d, st)
            emitir(ev, ctx, aviso)
        return
    if ev not in ("PostToolUse", "UserPromptSubmit"):
        return
    bloqueio = pausa(d, st)
    if bloqueio:
        salvar(d, st)
        saida({"decision": "block", "reason": bloqueio})
    ctx_c, aviso_c = conferir_handoff(d, st, raiz)
    nivel, pct, tok, janela = subiu_faixa(d, st)
    if nivel >= 2:
        pedir_handoff(st, raiz)
        medida = f"Contexto em {pct:.0f}% do ponto de compactação ({tok // 1000} mil de {janela // 1000} mil tokens)."
        if nivel == 2:
            ctx = f"{medida} Terminada a ação em curso, " + HANDOFF
        else:
            ctx = (f"{medida} Não abra trabalho novo: " + HANDOFF.replace(" e continue o trabalho.", ".")
                   + " Sugira ao usuário sessão nova + /prime.")
        salvar(d, st)
        emitir(ev, ctx, f"Contexto em {pct:.0f}% do ponto de compactação: o agente vai gravar o handoff.")
    salvar(d, st)
    emitir(ev, ctx_c, aviso_c)


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
    raiz = raiz_de(cwd)
    if ev == "SessionStart" and d.get("source") == "clear":
        return ao_limpar(d, raiz)
    st = carregar(d)
    if ev == "Stop":
        motivo = continuo(d, st, raiz)
        salvar(d, st)
        if motivo:
            saida({"decision": "block", "reason": motivo})
        return
    pastas = ativas(raiz)
    if not pastas:
        return sem_longrun(d, ev, st, raiz)
    lista = ", ".join(pastas)

    if ev == "PreCompact":
        saida({"systemMessage": f"Execução longa ativa ({lista}): a compactação vai resumir o histórico. "
                                "Garanta que state.md, progress.md e canal.md estão atualizados."})

    if ev == "SessionStart":
        extra, aviso = ("", None)
        if d.get("source") == "compact":
            extra, aviso = pos_compact(st, raiz, " " + HANDOFF_POS_COMPACT)
            salvar(d, st)
        emitir(ev, f"EXECUÇÃO LONGA ATIVA neste projeto ({lista}). O contexto foi compactado ou a sessão foi retomada: "
               "antes de qualquer ação, releia goal.md → state.md → plan.md → canal.md e as últimas linhas de "
               "progress.md e failures.md dessa pasta, e continue do primeiro item pendente sem reabrir o que já está feito."
               + extra, aviso)
        return

    if ev not in ("PostToolUse", "UserPromptSubmit"):
        return
    bloqueio = pausa(d, st)
    if bloqueio:
        salvar(d, st)
        saida({"decision": "block", "reason": bloqueio})
    ctx_c, aviso_c = conferir_handoff(d, st, raiz)
    nivel, pct, tok, janela = subiu_faixa(d, st)
    if not nivel:
        salvar(d, st)
        emitir(ev, ctx_c, aviso_c)
        return
    if nivel >= 2:
        pedir_handoff(st, raiz)
    salvar(d, st)

    canal = " e ".join(f"{p}/canal.md" for p in pastas)
    medida = f"Contexto em {pct:.0f}% do ponto de compactação ({tok // 1000} mil de {janela // 1000} mil tokens)."
    msgs = {
        1: (f"{medida} FAIXA 1 de 3: antes de seguir, acrescente em {canal} o que você precisaria se o histórico "
            "sumisse agora — fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas. Só acrescentar. "
            "Depois continue o trabalho normalmente.", None),
        2: (f"{medida} FAIXA 2 de 3: atualize state.md, progress.md e {canal}; termine a unidade de trabalho atual "
            "e grave o handoff agora (skill session-handoff, sem esperar pedido); depois avise o usuário que é hora de rodar /compact (compactar cedo resume melhor do que o automático perto do limite).",
            f"Execução longa em {pct:.0f}% do ponto de compactação: hora de /compact (o agente foi avisado)."),
        3: (f"{medida} FAIXA 3 de 3: não abra trabalho novo. Atualize state.md, progress.md e {canal} e peça ao usuário: "
            "/session-handoff, sessão nova e /prime (ou releitura da pasta longrun/). Sem humano por perto, siga só até o próximo checkpoint.",
            f"Execução longa em {pct:.0f}% do ponto de compactação: hora de /session-handoff + sessão nova + /prime."),
    }
    ctx, aviso = msgs[min(nivel, 3)]
    emitir(ev, ctx, aviso)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""nota-retomada.py — registra e compara quanto cada jeito de retomar uma sessão recuperou.

As 5 perguntas-teste do handoff (kit agente-claude-codex 1.5.2+) são respondidas por quem retoma:
  compactada  depois da compactação, de memória (só o resumo + o que ficou no contexto)
  retomada    depois de `claude --resume`, de memória
  continuada  ao reenviar depois de pausa com o cache vencido (a sessão antiga, relida inteira)
  prime       sessão nova com /clear + /prime (pelo handoff e pelos arquivos)

Uso (padrão desde 2026-10-20: o SCRIPT dá a nota, não o agente):
  nota-retomada.py --modo prime --respostas - --snapshot handoffs/history/<x>.md --raiz <dir> \
                   [--sessao <id>] [--tokens <contexto>] <<'FIM'
  1. <resposta>
  ...
  5. <resposta>
  FIM
  nota-retomada.py --relatorio [--dias 30]
  (antigo, autoavaliado: --acertos N [--total 5] — entra no relatório à parte)

Cada pergunta-teste do handoff termina com `— chave: \`valor\`` (aceita `a` | `b`). A resposta acerta se
contém uma chave (sem diferença de maiúscula/acento). Pergunta sem chave = "não conferida" (fora da conta).
Erro com a fonte da pergunta alterada depois do handoff (handoff-grava.py --conferir) = "desatualizado"
(o handoff envelheceu); erro com a fonte igual = "não recuperou" (a retomada perdeu a informação).
As respostas ficam gravadas no registro, para auditar depois.

Registro: uma linha JSON por medição em ~/.local/state/execucao-longa/notas.jsonl (LONGRUN_NOTAS muda).
"""
import argparse, json, os, pathlib, re, statistics, subprocess, sys, time, unicodedata

MODOS = ("compactada", "retomada", "continuada", "prime")
ARQ = pathlib.Path(os.environ.get("LONGRUN_NOTAS", pathlib.Path.home() / ".local/state/execucao-longa/notas.jsonl"))
SECOES = ("## Perguntas-teste", "## Test questions", "## Preguntas de control")
ITEM = re.compile(r"^\s*(\d)[.)]\s+(.*)$")
CHAVE = re.compile(r"\s[—-]\s*(?:chave|key|clave):\s*(.+)$", re.I)
FONTE = re.compile(r"\s[—-]\s*(?:fonte|source|fuente):\s*(.+?)(?=\s[—-]\s*(?:chave|key|clave):|$)", re.I)


def erro(msg):
    sys.exit(f"nota-retomada: {msg}")


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c)).replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def perguntas_do_handoff(txt):
    """{n: {"chaves": [...], "fontes": [...]}} da seção Perguntas-teste."""
    sec = next((s for s in SECOES if s in txt), None)
    if not sec:
        return {}
    bloco = txt.split(sec, 1)[1]
    bloco = re.split(r"^## ", bloco, maxsplit=1, flags=re.M)[0]
    out = {}
    for ln in bloco.splitlines():
        m = ITEM.match(ln)
        if not m:
            continue
        resto = m[2]
        ch = CHAVE.search(resto)
        chaves = [c for c in (x.strip().strip("`").strip() for x in ch[1].split("|")) if c and c not in ("—", "-")] \
            if ch else []
        fo = FONTE.search(resto)
        fontes = re.findall(r"`([^`\s]+)`", fo[1]) if fo else []
        if fo and not fontes:
            fontes = re.findall(r"[\w./-]+\.\w+", fo[1])
        out[int(m[1])] = {"chaves": chaves, "fontes": fontes}
    return out


def respostas_de(txt):
    out = {}
    for ln in txt.splitlines():
        m = ITEM.match(ln)
        if m:
            out[int(m[1])] = m[2].strip()
    return out


def grava_script():
    for p in (os.environ.get("HANDOFF_GRAVA"),
              pathlib.Path.home() / ".claude/skills/session-handoff/scripts/handoff-grava.py",
              pathlib.Path.home() / ".agents/skills/session-handoff/scripts/handoff-grava.py"):
        if p and pathlib.Path(p).is_file():
            return pathlib.Path(p)
    return None


def mudados(raiz, snapshot):
    """Arquivos que mudaram depois do handoff, pelo --conferir; None se não deu para conferir."""
    g = grava_script()
    if not g:
        return None
    r = subprocess.run([sys.executable, str(g), "--raiz", raiz, "--conferir", snapshot],
                       capture_output=True, text=True, timeout=120)
    if r.returncode not in (0, 2):
        return None
    return {m[1] for m in re.finditer(r"^\s+- ([^:]+): (?:mudou|sumiu)", r.stdout, re.M)}


def corrigir(raiz, snapshot, texto_resp):
    p = pathlib.Path(raiz) / snapshot
    try:
        hand = p.read_text(encoding="utf-8")
    except OSError:
        erro(f"snapshot ilegível: {p}")
    pergs = perguntas_do_handoff(hand)
    if not any(q["chaves"] for q in pergs.values()):
        erro("o handoff não tem chave em nenhuma pergunta-teste (`— chave: \\`valor\\``); "
             "sem chave não há nota do script — use --acertos (fica marcada como autoavaliada)")
    resp = respostas_de(texto_resp)
    mud = None
    itens = []
    for n in range(1, 6):
        q = pergs.get(n, {"chaves": [], "fontes": []})
        r = resp.get(n, "")
        if not q["chaves"]:
            res = "nao_conferida"
        elif any(norm(c) in norm(r) for c in q["chaves"]):
            res = "certa"
        else:
            if mud is None:
                mud = mudados(raiz, snapshot)
            res = "desatualizado" if mud and any(f in mud for f in q["fontes"]) else "nao_recuperou"
        itens.append({"n": n, "resposta": r, "chaves": q["chaves"], "fontes": q["fontes"], "resultado": res})
    return itens


def gravar(reg):
    ARQ.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQ, "a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


def base(a):
    return {"t": int(time.time()), "quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "modo": a.modo,
            "snapshot": a.snapshot, "raiz": a.raiz, "sessao": a.sessao, "tokens": a.tokens}


def registrar_script(a):
    if not a.snapshot or not a.raiz:
        erro("--respostas precisa de --snapshot e --raiz")
    texto = sys.stdin.read() if a.respostas == "-" else pathlib.Path(a.respostas).read_text(encoding="utf-8")
    itens = corrigir(a.raiz, a.snapshot, texto)
    conta = {k: sum(1 for i in itens if i["resultado"] == k)
             for k in ("certa", "desatualizado", "nao_recuperou", "nao_conferida")}
    total = 5 - conta["nao_conferida"]
    reg = {**base(a), "fonte_nota": "script", "acertos": conta["certa"], "total": total,
           "desatualizadas": conta["desatualizado"], "nao_recuperou": conta["nao_recuperou"],
           "nao_conferidas": conta["nao_conferida"], "perguntas": itens}
    gravar(reg)
    nomes = {"certa": "certa", "desatualizado": "errada — fonte mudou depois do handoff (desatualizado)",
             "nao_recuperou": "errada — não recuperou", "nao_conferida": "não conferida (sem chave)"}
    print(f"Nota da retomada (script): {conta['certa']}/{total} — {conta['desatualizado']} desatualizada(s), "
          f"{conta['nao_recuperou']} não recuperada(s), {conta['nao_conferida']} não conferida(s) → {ARQ}")
    for i in itens:
        print(f"  {i['n']}. {nomes[i['resultado']]}" + (f" (chave: {' | '.join(i['chaves'])})" if i["chaves"] else ""))


def registrar_agente(a):
    if not 0 <= a.acertos <= a.total:
        erro(f"acertos fora de 0..{a.total}")
    gravar({**base(a), "fonte_nota": "agente", "acertos": a.acertos, "total": a.total})
    print(f"nota registrada (autoavaliada, fora da média do script): {a.modo} {a.acertos}/{a.total} → {ARQ}")


def relatorio(dias):
    desde = time.time() - dias * 86400
    regs = []
    if ARQ.exists():
        for ln in ARQ.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("t", 0) >= desde:
                regs.append(r)
    scr = [r for r in regs if r.get("fonte_nota") == "script"]
    aut = [r for r in regs if r.get("fonte_nota") != "script"]
    print(f"Notas de retomada (últimos {dias} dias, {len(scr)} pelo script) — {ARQ}")
    print(f"{'modo':<11} {'n':>3} {'acerto':>7} {'desatualizado':>14} {'não recuperou':>14} {'tokens (mediana)':>17}")
    for m in MODOS:
        rs = [r for r in scr if r.get("modo") == m]
        if not rs:
            print(f"{m:<11} {0:>3} {'—':>7} {'—':>14} {'—':>14} {'—':>17}")
            continue
        tot = max(1, sum(r["total"] for r in rs))
        pct = 100 * sum(r["acertos"] for r in rs) / tot
        des = 100 * sum(r.get("desatualizadas", 0) for r in rs) / tot
        nrec = 100 * sum(r.get("nao_recuperou", 0) for r in rs) / tot
        toks = [r["tokens"] for r in rs if r.get("tokens")]
        med = f"{statistics.median(toks) / 1000:.0f} mil" if toks else "—"
        print(f"{m:<11} {len(rs):>3} {pct:>6.0f}% {des:>13.0f}% {nrec:>13.0f}% {med:>17}")
    if aut:
        pct = 100 * sum(r["acertos"] for r in aut) / max(1, sum(r["total"] for r in aut))
        print(f"autoavaliadas (nota dada pelo agente, fora da tabela): {len(aut)} medições, {pct:.0f}% de acerto declarado")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=MODOS)
    ap.add_argument("--respostas", help="arquivo com as 5 respostas ('1. ...'), ou - para ler do stdin")
    ap.add_argument("--acertos", type=int, help="(antigo) nota dada pelo agente; fica marcada como autoavaliada")
    ap.add_argument("--total", type=int, default=5)
    ap.add_argument("--snapshot", default="")
    ap.add_argument("--raiz", default="")
    ap.add_argument("--sessao", default="")
    ap.add_argument("--tokens", type=int, default=0)
    ap.add_argument("--relatorio", action="store_true")
    ap.add_argument("--dias", type=int, default=30)
    a = ap.parse_args()
    if a.relatorio:
        return relatorio(a.dias)
    if not a.modo:
        ap.error("--modo é obrigatório (ou --relatorio)")
    if a.respostas:
        return registrar_script(a)
    if a.acertos is None:
        ap.error("--respostas (nota do script) ou --acertos (autoavaliada)")
    registrar_agente(a)


if __name__ == "__main__":
    main()

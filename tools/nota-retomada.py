#!/usr/bin/env python3
"""nota-retomada.py — registra e compara quanto cada jeito de retomar uma sessão recuperou.

As 5 perguntas-teste do handoff (kit agente-claude-codex 1.5.2+) são respondidas por quem retoma:
  compactada  depois da compactação, de memória (só o resumo + o que ficou no contexto)
  retomada    depois de `claude --resume`, de memória
  continuada  ao reenviar depois de pausa com o cache vencido (a sessão antiga, relida inteira)
  prime       sessão nova com /clear + /prime (pelo handoff e pelos arquivos)

Uso:
  nota-retomada.py --modo compactada --acertos 4 [--total 5] --snapshot handoffs/history/<x>.md --raiz <dir>
                   [--sessao <id>] [--tokens <contexto no momento>]
  nota-retomada.py --relatorio [--dias 30]

Registro: uma linha JSON por medição em ~/.local/state/execucao-longa/notas.jsonl (LONGRUN_NOTAS muda).
Quem dá a nota é o próprio agente: as 5 respostas ficam escritas na conversa antes de ele abrir o handoff,
para que dê para auditar depois.
"""
import argparse, json, os, pathlib, statistics, sys, time

MODOS = ("compactada", "retomada", "continuada", "prime")
ARQ = pathlib.Path(os.environ.get("LONGRUN_NOTAS", pathlib.Path.home() / ".local/state/execucao-longa/notas.jsonl"))


def registrar(a):
    if not 0 <= a.acertos <= a.total:
        sys.exit(f"nota-retomada: acertos fora de 0..{a.total}")
    reg = {"t": int(time.time()), "quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "modo": a.modo,
           "acertos": a.acertos, "total": a.total, "snapshot": a.snapshot, "raiz": a.raiz,
           "sessao": a.sessao, "tokens": a.tokens}
    ARQ.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQ, "a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    print(f"nota registrada: {a.modo} {a.acertos}/{a.total} → {ARQ}")


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
    print(f"Notas de retomada (últimos {dias} dias, {len(regs)} medições) — {ARQ}")
    print(f"{'modo':<11} {'n':>3} {'acerto':>7} {'tokens (mediana)':>17}")
    for m in MODOS:
        rs = [r for r in regs if r.get("modo") == m]
        if not rs:
            print(f"{m:<11} {0:>3} {'—':>7} {'—':>17}")
            continue
        pct = 100 * sum(r["acertos"] for r in rs) / max(1, sum(r["total"] for r in rs))
        toks = [r["tokens"] for r in rs if r.get("tokens")]
        med = f"{statistics.median(toks) / 1000:.0f} mil" if toks else "—"
        print(f"{m:<11} {len(rs):>3} {pct:>6.0f}% {med:>17}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=MODOS)
    ap.add_argument("--acertos", type=int)
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
    if not a.modo or a.acertos is None:
        ap.error("--modo e --acertos são obrigatórios (ou --relatorio)")
    registrar(a)


if __name__ == "__main__":
    main()

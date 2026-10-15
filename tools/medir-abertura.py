#!/usr/bin/env python3
"""Mede o 1º turno das sessões do Claude Code: quanto da abertura veio do cache e quanto foi gravado de novo.

Uso: medir-abertura.py [--desde "AAAA-MM-DD HH:MM"] [--ate "AAAA-MM-DD HH:MM"] [--modelo opus-5-5] [--projeto wifi]
Compara períodos (ex.: antes e depois de ligar --exclude-dynamic-system-prompt-sections em 15/10/2026 04:00).
Só sessões interativas (entrypoint cli). Saída: mediana de lido, gravado, total e % lido.
"""
import argparse, datetime, glob, json, os, statistics as st


def ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return 0.0


def local(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M").timestamp() if s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde"); ap.add_argument("--ate")
    ap.add_argument("--modelo", default="opus-5-5"); ap.add_argument("--projeto", default="")
    a = ap.parse_args()
    ini, fim = local(a.desde), local(a.ate)
    linhas = []
    for f in glob.glob(os.path.expanduser(f"~/.claude/projects/*{a.projeto}*/*.jsonl")):
        if ini and os.path.getmtime(f) < ini:
            continue
        with open(f, errors="ignore") as fh:
            cab = [next(fh, "") for _ in range(400)]
        if not any('"entrypoint":"cli"' in l for l in cab) or not any(a.modelo in l for l in cab):
            continue
        for l in cab:
            if '"usage"' in l and '"assistant"' in l:
                try:
                    r = json.loads(l); u = r["message"]["usage"]
                except (ValueError, KeyError):
                    break
                t = ts(r.get("timestamp", ""))
                if (ini and t < ini) or (fim and t > fim):
                    break
                linhas.append((u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0)))
                break
    if not linhas:
        print("nenhuma sessão no período"); return
    lido = [x for x, _ in linhas]; grav = [y for _, y in linhas]
    pct = [x / (x + y) for x, y in linhas if x + y]
    print(f"sessões {len(linhas)} | lido med {st.median(lido)/1000:.1f} mil | gravado med {st.median(grav)/1000:.1f} mil | "
          f"total med {st.median([x + y for x, y in linhas])/1000:.1f} mil | % lido med {100*st.median(pct):.0f}% | "
          f"gravou <5 mil: {sum(1 for y in grav if y < 5000)}")


if __name__ == "__main__":
    main()

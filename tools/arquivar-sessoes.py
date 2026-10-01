#!/usr/bin/env python3
"""Higiene de sessões (F6): comprime JSONL antigos do Codex e do Claude Code num arquivo morto.

Padrão é SÓ RELATÓRIO. Com --aplicar: cada sessão elegível vira
~/.local/share/execucao-longa/arquivo/<fonte>/<caminho relativo>.jsonl.gz; o original só é
apagado depois de conferir que o .gz descomprime para os mesmos bytes (sha256).
--restaurar <arquivo.gz> devolve a sessão ao lugar original.

Nunca toca: sessões modificadas há menos de --dias, nem sessões de projetos com longrun ativo.
Atenção: sessão arquivada some do /resume (Claude) e do `codex resume` até ser restaurada.

Uso: tools/arquivar-sessoes.py [--dias 90] [--min-mb 0] [--aplicar] [--restaurar ARQ.gz]
"""
import argparse, gzip, hashlib, pathlib, re, shutil, sys, time

HOME = pathlib.Path.home()
FONTES = {"codex": HOME / ".codex/sessions", "claude": HOME / ".claude/projects"}
DESTINO = HOME / ".local/share/execucao-longa/arquivo"


def projetos_ativos():
    out = set()
    for s in (HOME / "projetos").glob("*/longrun/*/state.md"):
        t = s.read_text(errors="ignore").lower()
        if "concluído" not in t and "concluido" not in t:
            out.add(re.sub(r"[^A-Za-z0-9]", "-", str(s.parent.parent.parent)))  # mesmo nome que o Claude dá à pasta
    return out


def candidatos(dias, min_mb):
    lim, ativos = time.time() - dias * 86400, projetos_ativos()
    for fonte, base in FONTES.items():
        for f in base.rglob("*.jsonl"):
            st = f.stat()
            if st.st_mtime >= lim or st.st_size < min_mb * 1e6:
                continue
            if fonte == "claude" and f.relative_to(base).parts[0] in ativos:
                continue
            yield fonte, base, f, st.st_size


def sha(caminho, abrir=open):
    h = hashlib.sha256()
    with abrir(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def relatorio(min_mb):
    print(f"{'fonte':7} {'idade >':>8} {'sessões':>8} {'GB':>7}")
    for dias in (30, 60, 90, 180):
        por = {}
        for fonte, _, _, tam in candidatos(dias, min_mb):
            n, b = por.get(fonte, (0, 0))
            por[fonte] = (n + 1, b + tam)
        for fonte in FONTES:
            n, b = por.get(fonte, (0, 0))
            print(f"{fonte:7} {dias:>6} d {n:>8} {b / 1e9:>7.2f}")


def aplicar(dias, min_mb):
    total = ganho = 0
    for fonte, base, f, tam in candidatos(dias, min_mb):
        alvo = DESTINO / fonte / (str(f.relative_to(base)) + ".gz")
        alvo.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "rb") as src, gzip.open(alvo, "wb", compresslevel=6) as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
        if sha(f) != sha(alvo, gzip.open):
            alvo.unlink()
            print(f"ERRO de conferência, original mantido: {f}", file=sys.stderr)
            continue
        f.unlink()
        total += 1
        ganho += tam - alvo.stat().st_size
        print(f"arquivado: {f} → {alvo}")
    print(f"{total} sessões arquivadas, {ganho / 1e9:.2f} GB liberados")


def restaurar(gz):
    gz = pathlib.Path(gz).expanduser().resolve()
    rel = gz.relative_to(DESTINO)
    fonte, resto = rel.parts[0], pathlib.Path(*rel.parts[1:])
    orig = FONTES[fonte] / str(resto)[: -len(".gz")]
    orig.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(gz, "rb") as src, open(orig, "wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    gz.unlink()
    print(f"restaurado: {orig}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=float, default=90)
    ap.add_argument("--min-mb", type=float, default=0)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--restaurar")
    a = ap.parse_args()
    if a.restaurar:
        restaurar(a.restaurar)
    elif a.aplicar:
        aplicar(a.dias, a.min_mb)
    else:
        relatorio(a.min_mb)
        print("\n(só relatório; use --aplicar --dias N para arquivar)")


if __name__ == "__main__":
    main()

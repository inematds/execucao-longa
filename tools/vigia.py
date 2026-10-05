#!/usr/bin/env python3
"""Vigia de execuções longas (F5).

Procura execuções ativas (longrun/*/state.md sem "concluído") nos projetos e alerta quando:
  - PARADO: o loop-longrun.sh registrou parada (estagnação, teto de ciclos) no loop.log;
  - PARADO SEM AVISO: a pasta tem loop.log mas nenhum processo do loop está vivo nela;
  - OCIOSA: nada mudou na pasta e nenhuma sessão (Codex/Claude) gravou eventos há mais de N minutos.
Cada problema alerta uma vez (estado em ~/.local/state/execucao-longa/vigia.json) e volta a alertar
só depois de resolvido. Alerta = linha em ~/.local/state/execucao-longa/alertas.log (+ notify-send só com --desktop).
--notificar-cmd permite plugar outro canal (ex.: Telegram) — só com autorização para essa API.

Uso: tools/vigia.py [--raiz ~/projetos] [--ocioso-min 30] [--notificar-cmd CMD] [--seco]
"""
import argparse, json, os, pathlib, re, shlex, subprocess, sys, time

ESTADO_DIR = pathlib.Path(os.environ.get("VIGIA_ESTADO", pathlib.Path.home() / ".local/state/execucao-longa"))
SESSOES = [pathlib.Path.home() / ".codex/sessions", pathlib.Path.home() / ".claude/projects"]


def ativas(raiz):
    for s in sorted(raiz.glob("*/longrun/*/state.md")):
        txt = s.read_text(errors="ignore").lower()
        if "concluído" not in txt and "concluido" not in txt:
            yield s.parent


def ultima_mudanca(pasta):
    return max((p.stat().st_mtime for p in pasta.rglob("*") if p.is_file()), default=0)


def ultima_sessao(projeto):
    """Evento mais recente: sessões do Claude deste projeto ou qualquer sessão do Codex de hoje."""
    t = 0
    pasta_cc = SESSOES[1] / re.sub(r"[^A-Za-z0-9]", "-", str(projeto))  # nome que o Claude dá à pasta
    for base, padrao in ((pasta_cc, "*.jsonl"), (SESSOES[0], "**/*.jsonl")):
        if not base.exists():
            continue
        for f in base.glob(padrao):
            m = f.stat().st_mtime
            if m > t and (base == pasta_cc or time.time() - m < 86400):
                t = m
    return t


def loop_vivo(pasta):
    """O loop-longrun.sh segura flock em .loop.lock enquanto roda: lock preso = loop vivo."""
    lock = pasta / ".loop.lock"
    if not lock.exists():
        return False
    return subprocess.run(["flock", "-n", str(lock), "true"]).returncode != 0


def diagnosticar(pasta, ocioso_min, agora):
    log = pasta / "loop.log"
    if log.exists():
        linhas = log.read_text(errors="ignore").strip().splitlines()
        ultima = linhas[-1] if linhas else ""
        if "PARADO" in ultima:
            return "parado", ultima
        if "CONCLUÍDO" not in ultima and not loop_vivo(pasta):
            return "parado-sem-aviso", f"loop.log sem fim registrado e nenhum loop vivo (última linha: {ultima[:120]})"
    ref = max(ultima_mudanca(pasta), ultima_sessao(pasta.parent.parent))
    ocioso = (agora - ref) / 60
    if ocioso > ocioso_min:
        return "ociosa", f"{ocioso:.0f} min sem mudança na pasta nem eventos de sessão (limite {ocioso_min})"
    return None, None


def alertar(msg, cmd, seco, desktop=False):
    print(msg)
    if seco:
        return
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    with open(ESTADO_DIR / "alertas.log", "a") as f:
        f.write(f"{time.strftime('%F %T')} {msg}\n")
    if desktop:  # opt-in: pop-up crítico acumulava no topo da tela (05/10/2026)
        subprocess.run(["notify-send", "-u", "critical", "Execução longa", msg], capture_output=True)
    if cmd:
        subprocess.run(shlex.split(cmd) + [msg], capture_output=True, timeout=60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=str(pathlib.Path.home() / "projetos"))
    ap.add_argument("--ocioso-min", type=float, default=30)
    ap.add_argument("--notificar-cmd", default="")
    ap.add_argument("--desktop", action="store_true", help="também mostra pop-up (notify-send)")
    ap.add_argument("--seco", action="store_true", help="só imprime, não grava nem notifica")
    a = ap.parse_args()

    estado_f = ESTADO_DIR / "vigia.json"
    try:
        estado = json.loads(estado_f.read_text())
    except (OSError, ValueError):
        estado = {}
    agora, novo, n = time.time(), {}, 0
    for pasta in ativas(pathlib.Path(a.raiz).expanduser()):
        n += 1
        tipo, detalhe = diagnosticar(pasta, a.ocioso_min, agora)
        if not tipo:
            continue
        chave = f"{pasta}:{tipo}"
        novo[chave] = estado.get(chave, agora)
        if chave not in estado:
            alertar(f"[{tipo}] {pasta}: {detalhe}", a.notificar_cmd, a.seco, a.desktop)
    if not a.seco:
        ESTADO_DIR.mkdir(parents=True, exist_ok=True)
        estado_f.write_text(json.dumps(novo, indent=1))
    print(f"vigia: {n} execução(ões) ativa(s), {len(novo)} com problema", file=sys.stderr)


if __name__ == "__main__":
    main()

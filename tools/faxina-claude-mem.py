#!/usr/bin/env python3
"""Faxina do claude-mem (F9). Padrão: SÓ RELATÓRIO.

Com --aplicar (tudo reversível):
  1. backup consistente do banco (API de backup do SQLite) em ~/.claude-mem/backups/;
  2. numa transação: apaga da fila `pending_messages` só o que tem mais de --dias (padrão 30) e
     marca como `completed` as sessões `active` iniciadas há mais de --dias que não têm pendência recente;
  3. comprime com gzip os logs de ~/.claude-mem/logs com mais de --dias-log (padrão 14), menos o do dia;
  4. move o aviso antigo CAPTURE_BROKEN para backups/.
Não reprocessa nada (reprocessar passaria ~120 MB pelo Haiku, gastando cota, para lotes automáticos de baixo valor).
Para desfazer: pare o worker, copie o backup de volta para ~/.claude-mem/claude-mem.db e gunzip os logs.

Uso: tools/faxina-claude-mem.py [--dias 30] [--dias-log 14] [--aplicar]
"""
import argparse, gzip, os, pathlib, shutil, sqlite3, time

BASE = pathlib.Path(os.environ.get("CLAUDE_MEM_DIR", pathlib.Path.home() / ".claude-mem"))
DB = BASE / "claude-mem.db"


def relatorio(c, corte_ms, corte_log):
    q = lambda s, *a: c.execute(s, a).fetchone()[0]
    pend = q("select count(*) from pending_messages where created_at_epoch < ?", corte_ms)
    pend_rec = q("select count(*) from pending_messages where created_at_epoch >= ?", corte_ms)
    presas = q("""select count(*) from sdk_sessions s where status='active' and started_at_epoch < ?
                  and not exists (select 1 from pending_messages p where p.session_db_id=s.id and p.created_at_epoch >= ?)""",
               corte_ms, corte_ms)
    logs = [f for f in (BASE / "logs").glob("*.log") if f.stat().st_mtime < corte_log]
    mb = sum(f.stat().st_size for f in logs) / 1e6
    print(f"pendências antigas (> corte): {pend}   recentes (mantidas): {pend_rec}")
    print(f"sessões 'active' antigas sem pendência recente: {presas}")
    print(f"logs para comprimir: {len(logs)} arquivos, {mb:.0f} MB")
    print(f"aviso CAPTURE_BROKEN: {'existe' if (BASE / 'CAPTURE_BROKEN').exists() else 'não'}")
    return logs


def aplicar(c, corte_ms, logs):
    bk = BASE / "backups" / f"claude-mem-{time.strftime('%Y%m%d-%H%M%S')}-pre-faxina.db"
    bk.parent.mkdir(exist_ok=True)
    destino = sqlite3.connect(bk)
    c.backup(destino)
    destino.close()
    chk = sqlite3.connect(f"file:{bk}?mode=ro", uri=True).execute("pragma quick_check").fetchone()[0]
    if chk != "ok":
        raise SystemExit(f"backup com problema ({chk}); nada foi alterado")
    print(f"backup: {bk} ({bk.stat().st_size / 1e6:.0f} MB, quick_check ok)")
    with c:  # transação única
        n1 = c.execute("""update sdk_sessions set status='completed' where status='active' and started_at_epoch < ?
                          and not exists (select 1 from pending_messages p where p.session_db_id=sdk_sessions.id
                                          and p.created_at_epoch >= ?)""", (corte_ms, corte_ms)).rowcount
        n2 = c.execute("delete from pending_messages where created_at_epoch < ?", (corte_ms,)).rowcount
    print(f"sessões fechadas: {n1}   pendências removidas: {n2}")
    hoje = time.strftime("%Y-%m-%d")
    lib = 0
    for f in logs:
        if hoje in f.name:
            continue
        with open(f, "rb") as src, gzip.open(str(f) + ".gz", "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
        lib += f.stat().st_size - pathlib.Path(str(f) + ".gz").stat().st_size
        f.unlink()
    print(f"logs comprimidos: {len(logs)}, {lib / 1e6:.0f} MB liberados")
    aviso = BASE / "CAPTURE_BROKEN"
    if aviso.exists():
        shutil.move(aviso, BASE / "backups" / "CAPTURE_BROKEN.2026-05-06")
        print("CAPTURE_BROKEN movido para backups/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=float, default=30)
    ap.add_argument("--dias-log", type=float, default=14)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    agora = time.time()
    corte_ms, corte_log = int((agora - a.dias * 86400) * 1000), agora - a.dias_log * 86400
    c = sqlite3.connect(DB, timeout=60)
    c.execute("pragma busy_timeout=60000")
    logs = relatorio(c, corte_ms, corte_log)
    if a.aplicar:
        aplicar(c, corte_ms, logs)
        print("\ndepois:")
        relatorio(c, corte_ms, corte_log)
    else:
        print("\n(só relatório; use --aplicar)")


if __name__ == "__main__":
    main()

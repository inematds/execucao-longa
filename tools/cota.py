#!/usr/bin/env python3
"""Trava de cota compartilhada (17/11/2026): consulta, sem chamar modelo, se a assinatura está
sem cota. Mesma tabela `pools` do EngineBridge e do ia_motor.py dos crons
(~/.local/state/enginebridge/state.sqlite; INEMA_COTA_DB muda o caminho). Quem grava a trava é o
ia_motor.py/openpcbotv3 ao receber a recusa estruturada; aqui só se respeita.

uso: cota.py claude|codex   → sai 0 se livre; 75 e imprime "sem cota até DD/MM HH:MM" se travada.
Falha de leitura do banco = livre (a trava é proteção, não portão)."""
import datetime as dt
import os
import sqlite3
import sys
import time
from pathlib import Path


def pool(motor):
    if motor == 'claude':
        return 'claude:' + str(Path(os.environ.get('CLAUDE_CONFIG_DIR', Path.home() / '.claude')).expanduser())
    return 'codex:' + str(Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).expanduser().resolve())


def travada(motor, agora=None):
    """None se livre; texto do motivo se travada."""
    p = Path(os.environ.get('INEMA_COTA_DB', Path.home() / '.local/state/enginebridge/state.sqlite')).expanduser()
    if not p.exists():
        return None
    try:
        with sqlite3.connect(p, timeout=10) as db:
            linha = db.execute('SELECT blocked, until FROM pools WHERE pool=?', (pool(motor),)).fetchone()
    except sqlite3.Error:
        return None
    if linha and linha[0]:
        return f'{motor} com bloqueio manual'
    if linha and linha[1] > (agora or time.time()):
        return f'{motor} sem cota até ' + dt.datetime.fromtimestamp(linha[1]).strftime('%d/%m %H:%M')
    return None


if __name__ == '__main__':
    motivo = travada(sys.argv[1] if len(sys.argv) > 1 else 'claude')
    if motivo:
        print(motivo)
        sys.exit(75)

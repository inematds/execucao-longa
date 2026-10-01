#!/usr/bin/env bash
# Repasse: a lógica está em hook-longrun.py (faixas de contexto, aviso antes/depois de compactar).
exec python3 "$(dirname "$0")/hook-longrun.py"

#!/usr/bin/env python3
"""custo-retomada.py — custo real de voltar a trabalhar: (A) reenviar numa sessão grande com o cache vencido
(> 60 min parada, contexto >= 150 mil) × (B) sessão nova que começa com /prime. Lê ~/.claude/projects/*/*.jsonl.
Uso: custo-retomada.py [dias=14]
Unidade: tokens equivalentes ao preço de entrada = input + escrita_5m*1,25 + escrita_1h*2 + leitura*0,1.
Par do nota-retomada.py (quanto cada caminho recupera).
"""
import json, glob, os, sys, time
from datetime import datetime

DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 14
lim = time.time() - DIAS * 86400
arqs = [f for f in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')) if os.path.getmtime(f) > lim]

def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()

def custo(u):
    cc = u.get('cache_creation') or {}
    w1h = cc.get('ephemeral_1h_input_tokens', 0)
    w5m = cc.get('ephemeral_5m_input_tokens', 0)
    wtot = u.get('cache_creation_input_tokens', 0)
    if not (w1h or w5m):
        w1h = wtot  # Claude Code usa TTL de 1 h aqui
    return u.get('input_tokens', 0) + 1.25 * w5m + 2 * w1h + 0.1 * u.get('cache_read_input_tokens', 0)

def ctx(u):
    return u.get('input_tokens', 0) + u.get('cache_creation_input_tokens', 0) + u.get('cache_read_input_tokens', 0)

retomadas, primes = [], []
for f in arqs:
    eventos = []
    vistos = set()
    try:
        for ln in open(f, errors='ignore'):
            try:
                d = json.loads(ln)
            except Exception:
                continue
            t = d.get('type')
            if t == 'user' and not d.get('isMeta'):
                m = d.get('message', {})
                c = m.get('content')
                txt = c if isinstance(c, str) else ''
                if isinstance(c, list):
                    if any(x.get('type') == 'tool_result' for x in c if isinstance(x, dict)):
                        continue
                    txt = ' '.join(x.get('text', '') for x in c if isinstance(x, dict))
                eventos.append(('u', ts(d['timestamp']), txt))
            elif t == 'assistant':
                m = d.get('message', {})
                mid = m.get('id')
                if mid in vistos or not m.get('usage'):
                    continue
                vistos.add(mid)
                eventos.append(('a', ts(d['timestamp']), m['usage']))
    except Exception:
        continue
    # (A) retomada após pausa > 60 min com contexto >= 150 mil: custo da 1ª chamada
    ult_a, ult_ctx = None, 0
    for i, e in enumerate(eventos):
        if e[0] == 'a':
            ult_a, ult_ctx = e[1], ctx(e[2])
        elif e[0] == 'u' and ult_a and e[1] - ult_a > 3600 and ult_ctx >= 150000:
            prox = next((x for x in eventos[i + 1:] if x[0] == 'a'), None)
            if prox:
                retomadas.append((ult_ctx, custo(prox[2]), prox[2].get('cache_read_input_tokens', 0)))
    # (B) sessão que começa com /prime: custo até a 1ª mensagem seguinte do usuário
    us = [e for e in eventos if e[0] == 'u']
    if us and ('prime' in us[0][2][:300].lower()):
        i0 = eventos.index(us[0])
        tot, n, fim_ctx = 0, 0, 0
        for e in eventos[i0 + 1:]:
            if e[0] == 'u':
                break
            tot += custo(e[2]); n += 1; fim_ctx = ctx(e[2])
        if n:
            primes.append((tot, n, fim_ctx))

def med(v):
    v = sorted(v); return v[len(v) // 2] if v else 0

print(f'arquivos {len(arqs)} (últimos {DIAS} dias)')
print(f'(A) retomadas com cache vencido: {len(retomadas)}')
if retomadas:
    print('   contexto mediano', round(med([r[0] for r in retomadas]) / 1000), 'mil; custo mediano 1ª chamada',
          round(med([r[1] for r in retomadas]) / 1000), 'mil eq; leitura de cache mediana',
          round(med([r[2] for r in retomadas]) / 1000), 'mil')
    print('   faixa custo', round(min(r[1] for r in retomadas) / 1000), '-', round(max(r[1] for r in retomadas) / 1000), 'mil eq')
print(f'(B) sessões que começam com prime: {len(primes)}')
if primes:
    print('   custo mediano do prime', round(med([p[0] for p in primes]) / 1000), 'mil eq; chamadas medianas', med([p[1] for p in primes]),
          '; contexto no fim', round(med([p[2] for p in primes]) / 1000), 'mil')
    print('   faixa', round(min(p[0] for p in primes) / 1000), '-', round(max(p[0] for p in primes) / 1000), 'mil eq')

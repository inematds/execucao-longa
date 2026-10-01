#!/usr/bin/env python3
"""Busca local e incremental nas transcrições do Codex e Claude Code."""
import argparse
import gzip
import json
import os
from pathlib import Path
import sqlite3
import sys


SCHEMA = """
CREATE TABLE IF NOT EXISTS arquivos (
    arquivo TEXT PRIMARY KEY, fonte TEXT NOT NULL, tamanho INTEGER NOT NULL,
    mtime INTEGER NOT NULL, posicao INTEGER NOT NULL, linha INTEGER NOT NULL,
    projeto TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS trechos USING fts5(
    texto, data UNINDEXED, fonte UNINDEXED, projeto UNINDEXED,
    papel UNINDEXED, arquivo UNINDEXED, linha UNINDEXED,
    tokenize='unicode61 remove_diacritics 2'
);
"""
CODEX_META = ('# AGENTS.md instructions', '<environment_context>',
              '<user_instructions>', '<INSTRUCTIONS>')
CLAUDE_META = ('<system-reminder>', '<command-', '<local-command')


def textos(content, tipos):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ''
    return '\n'.join(b['text'] for b in content if isinstance(b, dict)
                     and b.get('type') in tipos and isinstance(b.get('text'), str))


def extrair(obj, fonte, projeto):
    """Retorna projeto atualizado e pares papel/texto; nunca inclui tool output."""
    saida = []
    tipo = obj.get('type')
    if fonte == 'codex':
        p = obj.get('payload')
        if not isinstance(p, dict):
            return projeto, saida
        if tipo in ('session_meta', 'turn_context') and isinstance(p.get('cwd'), str):
            projeto = Path(p['cwd']).name
        if tipo != 'response_item':
            return projeto, saida
        if p.get('type') == 'message' and p.get('role') in ('user', 'assistant'):
            papel = p['role']
            texto = textos(p.get('content'), ('input_text', 'output_text'))
            if texto and not (papel == 'user' and texto.lstrip().startswith(CODEX_META)):
                saida.append((papel, texto))
        elif p.get('type') in ('function_call', 'custom_tool_call'):
            argumento = p.get('arguments') or p.get('input') or ''
            if not isinstance(argumento, str):
                argumento = json.dumps(argumento, ensure_ascii=False)
            saida.append(('ferramenta', str(p.get('name', '')) + ' ' + argumento[:300]))
    else:
        projeto = Path(obj.get('cwd') or '').name
        msg = obj.get('message')
        if not isinstance(msg, dict):
            return projeto, saida
        content = msg.get('content')
        if tipo == 'user' and not obj.get('isMeta'):
            texto = textos(content, ('text',))
            if texto and not texto.lstrip().startswith(CLAUDE_META):
                saida.append(('user', texto))
        elif tipo == 'assistant':
            texto = textos(content, ('text',))
            if texto:
                saida.append(('assistant', texto))
            if isinstance(content, list):
                for bloco in content:
                    if isinstance(bloco, dict) and bloco.get('type') == 'tool_use':
                        saida.append(('ferramenta', str(bloco.get('name', '')) + ' ' +
                                      json.dumps(bloco.get('input', {}))[:300]))
    return projeto, saida


def candidatos(args):
    vistos = set()
    for fonte, raiz, padrao in [('codex', args.codex, '*.jsonl'),
                                ('claude', args.claude, '*.jsonl'),
                                (None, args.arquivo, '*.jsonl.gz')]:
        raiz = Path(raiz).expanduser()
        for p in raiz.rglob(padrao):
            origem = fonte or p.relative_to(raiz).parts[0]
            if origem not in ('codex', 'claude') or not p.is_file():
                continue
            p = p.resolve()
            if p not in vistos:
                vistos.add(p)
                yield p, origem


def indexar(db, args):
    db.parent.mkdir(parents=True, exist_ok=True)
    arquivos = novos = 0
    with sqlite3.connect(db) as conn:
        conn.executescript(SCHEMA)
        for path, fonte in candidatos(args):
            stat = path.stat()
            anterior = conn.execute('SELECT fonte,tamanho,mtime,posicao,linha,projeto '
                                    'FROM arquivos WHERE arquivo=?', (str(path),)).fetchone()
            gz = path.suffix == '.gz'
            if anterior and anterior[:3] == (fonte, stat.st_size, stat.st_mtime_ns):
                continue
            reiniciar = (not anterior or anterior[0] != fonte or gz or
                         stat.st_size < anterior[1] or
                         (stat.st_size == anterior[1] and stat.st_mtime_ns != anterior[2]))
            posicao, linha, projeto = (0, 0, '') if reiniciar else anterior[3:]
            with conn:
                if anterior and reiniciar:
                    conn.execute('DELETE FROM trechos WHERE arquivo=?', (str(path),))
                with (gzip.open(path, 'rb') if gz else path.open('rb')) as stream:
                    stream.seek(posicao)
                    while True:
                        raw = stream.readline()
                        if not raw:
                            break
                        linha += 1
                        posicao = stream.tell()
                        try:
                            obj = json.loads(raw)
                        except (ValueError, UnicodeError):
                            continue
                        if not isinstance(obj, dict):
                            continue
                        projeto, itens = extrair(obj, fonte, projeto)
                        data = obj.get('timestamp')
                        data = data if isinstance(data, str) else ''
                        for papel, texto in itens:
                            conn.execute('INSERT INTO trechos VALUES (?,?,?,?,?,?,?)',
                                         (texto, data, fonte, projeto, papel, str(path), linha))
                            novos += 1
                conn.execute('INSERT OR REPLACE INTO arquivos VALUES (?,?,?,?,?,?,?)',
                             (str(path), fonte, stat.st_size, stat.st_mtime_ns,
                              posicao, linha, projeto))
            arquivos += 1
    print(f'{arquivos} arquivos processados; {novos} trechos novos.')


def buscar(db, args):
    if not db.is_file():
        raise ValueError('Índice ausente: execute recall.py indexar primeiro.')
    tokens = ' '.join(args.termos).split()
    consulta = ' AND '.join('"' + t.replace('"', '""') + '"' for t in tokens)
    resultados = []
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='trechos'").fetchone():
            raise ValueError('Índice ausente: execute recall.py indexar primeiro.')
        if consulta:
            filtros = ['trechos MATCH ?']
            valores = [consulta]
            for campo in ('projeto', 'fonte', 'papel', 'desde'):
                valor = getattr(args, campo)
                if valor:
                    filtros.append('data >= ?' if campo == 'desde' else campo + ' = ?')
                    valores.append(valor)
            valores.append(args.n)
            sql = ("SELECT data,fonte,projeto,papel,snippet(trechos,0,'','','…',40),arquivo,linha "
                   'FROM trechos WHERE ' + ' AND '.join(filtros) +
                   ' ORDER BY bm25(trechos),data DESC LIMIT ?')
            for row in conn.execute(sql, valores):
                item = dict(zip(('data', 'fonte', 'projeto', 'papel', 'trecho', 'arquivo', 'linha'), row))
                item['trecho'] = item['trecho'][:300]
                resultados.append(item)
    if args.json:
        print(json.dumps(resultados, ensure_ascii=False))
    else:
        for r in resultados:
            trecho = ' '.join(r['trecho'].split())
            print(f"{r['data']} {r['fonte']} {r['projeto']} {r['papel']} {trecho} {r['arquivo']}:{r['linha']}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in ('indexar', 'buscar', '-h', '--help'):
        argv.insert(0, 'buscar')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='comando', required=True)
    idx = sub.add_parser('indexar', help='Indexar transcrições locais')
    idx.add_argument('--codex', default='~/.codex/sessions')
    idx.add_argument('--claude', default='~/.claude/projects')
    idx.add_argument('--arquivo', default='~/.local/share/execucao-longa/arquivo')
    search = sub.add_parser('buscar', help='Buscar termos no índice')
    search.add_argument('termos', nargs='+')
    search.add_argument('--projeto')
    search.add_argument('--fonte', choices=('codex', 'claude'))
    search.add_argument('--papel', choices=('user', 'assistant', 'ferramenta'))
    search.add_argument('--desde')
    search.add_argument('-n', type=int, default=20)
    search.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    if args.comando == 'buscar' and args.n < 0:
        parser.error('-n deve ser maior ou igual a zero')
    db = Path(os.environ.get('RECALL_DB', '~/.local/share/execucao-longa/recall.db')).expanduser().resolve()
    try:
        (indexar if args.comando == 'indexar' else buscar)(db, args)
    except (OSError, sqlite3.Error, ValueError, EOFError) as exc:
        print(f'recall: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

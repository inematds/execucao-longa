#!/usr/bin/env python3
"""Mede sessões JSONL de Codex e Claude Code usando apenas a biblioteca padrão."""

import argparse
from datetime import datetime
import json
import sys


def tamanho(valor):
    """Tamanho da saída decodificada, com a serialização JSON padrão."""
    if not isinstance(valor, str):
        valor = json.dumps(valor, ensure_ascii=False)
    return len(valor.encode("utf-8"))


def razao(cached, entrada):
    return cached / entrada if entrada else 0.0


def ponto(i, timestamp, entrada, cached, compactacoes):
    return dict(i=i, timestamp=timestamp, input=entrada, cached=cached,
                ratio=razao(cached, entrada), compactacoes=compactacoes)


def duracao(inicio, fim):
    try:
        return int((datetime.fromisoformat(fim.replace("Z", "+00:00"))
                    - datetime.fromisoformat(inicio.replace("Z", "+00:00")))
                   .total_seconds())
    except (ValueError, TypeError, AttributeError):
        return 0


def medir(arquivo, por_turno=False):
    resultado = dict(fonte=None, arquivo=arquivo, bytes=0, linhas=0,
                     inicio=None, fim=None, duracao_s=0, compactacoes=0,
                     input_tokens=0, cached_tokens=0, cache_write_tokens=0,
                     output_tokens=0, cache_ratio=0.0,
                     bytes_saida_ferramenta=0, modelos=[], turnos=0)
    modelos = set()
    curva = []
    mensagens = {}
    with open(arquivo, "rb") as linhas:
        for linha in linhas:
            resultado["linhas"] += 1
            resultado["bytes"] += len(linha)
            try:
                registro = json.loads(linha)
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(registro, dict):
                continue
            timestamp = registro.get("timestamp")
            if isinstance(timestamp, str):
                if resultado["inicio"] is None:
                    resultado["inicio"] = timestamp
                resultado["fim"] = timestamp
            tipo = registro.get("type")
            if resultado["fonte"] is None:
                if tipo in ("session_meta", "turn_context", "response_item", "event_msg"):
                    resultado["fonte"] = "codex"
                elif tipo in ("user", "assistant") and "message" in registro:
                    resultado["fonte"] = "claude"

            # Fronteiras podem preceder a primeira linha que identifica a fonte.
            if tipo == "compacted" or (tipo == "system" and
                                       registro.get("subtype") == "compact_boundary"):
                resultado["compactacoes"] += 1

            if resultado["fonte"] == "codex":
                payload = registro.get("payload")
                if not isinstance(payload, dict):
                    continue
                if tipo == "turn_context" and payload.get("model"):
                    modelos.add(payload["model"])
                if tipo == "response_item" and payload.get("type") in (
                        "function_call_output", "custom_tool_call_output"):
                    resultado["bytes_saida_ferramenta"] += tamanho(payload.get("output"))
                info = payload.get("info")
                if (tipo == "event_msg" and payload.get("type") == "token_count"
                        and isinstance(info, dict)):
                    resultado["turnos"] += 1
                    total = info.get("total_token_usage") or {}
                    for destino, origem in (
                            ("input_tokens", "input_tokens"),
                            ("cached_tokens", "cached_input_tokens"),
                            ("cache_write_tokens", "cache_write_input_tokens"),
                            ("output_tokens", "output_tokens")):
                        resultado[destino] = total.get(origem, 0)
                    if por_turno:
                        uso = info.get("last_token_usage") or {}
                        curva.append(ponto(resultado["turnos"], timestamp,
                                           uso.get("input_tokens", 0),
                                           uso.get("cached_input_tokens", 0),
                                           resultado["compactacoes"]))

            elif resultado["fonte"] == "claude":
                mensagem = registro.get("message")
                if not isinstance(mensagem, dict):
                    continue
                if tipo == "user":
                    conteudo = mensagem.get("content")
                    if isinstance(conteudo, list):
                        for bloco in conteudo:
                            if isinstance(bloco, dict) and bloco.get("type") == "tool_result":
                                resultado["bytes_saida_ferramenta"] += tamanho(bloco.get("content"))
                uso = mensagem.get("usage")
                if tipo == "assistant" and isinstance(uso, dict):
                    modelo = mensagem.get("model")
                    if modelo and modelo != "<synthetic>":
                        modelos.add(modelo)
                    identificador = mensagem.get("id")
                    if identificador not in mensagens:
                        mensagens[identificador] = [timestamp, resultado["compactacoes"], None]
                    # Não reter conteúdo, apenas quatro contadores por id.
                    cached = uso.get("cache_read_input_tokens", 0)
                    escrita = uso.get("cache_creation_input_tokens", 0)
                    entrada = uso.get("input_tokens", 0) + cached + escrita
                    mensagens[identificador][2] = (entrada, cached, escrita,
                                                  uso.get("output_tokens", 0))

    if resultado["fonte"] == "claude":
        resultado["turnos"] = len(mensagens)
        for i, (timestamp, compactacoes, uso) in enumerate(mensagens.values(), 1):
            for campo, valor in zip(("input_tokens", "cached_tokens", "cache_write_tokens",
                                     "output_tokens"), uso):
                resultado[campo] += valor
            if por_turno:
                curva.append(ponto(i, timestamp, uso[0], uso[1], compactacoes))
    resultado["duracao_s"] = duracao(resultado["inicio"], resultado["fim"])
    resultado["modelos"] = sorted(modelos)
    resultado["cache_ratio"] = razao(resultado["cached_tokens"], resultado["input_tokens"])
    return curva if por_turno else resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arquivos", nargs="+", metavar="arquivo.jsonl")
    parser.add_argument("--json", action="store_true", help="saída estruturada JSON")
    parser.add_argument("--por-turno", action="store_true", help="curva por turno (com --json)")
    args = parser.parse_args()
    if args.por_turno and not args.json:
        parser.error("--por-turno requer --json")
    try:
        resultados = [medir(arquivo, args.por_turno) for arquivo in args.arquivos]
    except FileNotFoundError as erro:
        print(f"Arquivo não encontrado: {erro.filename}", file=sys.stderr)
        return 1
    except OSError as erro:
        print(f"Erro ao ler arquivo: {erro}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(resultados[0] if len(resultados) == 1 else resultados,
                         ensure_ascii=False))
    else:
        for r in resultados:
            print(f"{r['arquivo']} ({r['fonte'] or 'desconhecida'})\n"
                  f"  duração: {r['duracao_s']} s | compactações: {r['compactacoes']} | "
                  f"turnos: {r['turnos']}\n"
                  f"  tokens de entrada: {r['input_tokens']} | saída: {r['output_tokens']} | "
                  f"cache: {r['cache_ratio']:.1%}\n"
                  f"  cache lido: {r['cached_tokens']} | escrito: {r['cache_write_tokens']} | "
                  f"saída de ferramenta: {r['bytes_saida_ferramenta']} bytes\n"
                  f"  modelos: {', '.join(r['modelos'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

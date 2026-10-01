"""Testes CONGELADOS do piloto F1 (longrun/2026-10-01-medir-sessao). O agente não pode alterar esta pasta.

Teste rápido por ciclo:  pytest -q -m "not real"
Teste completo no final: pytest -q
"""
import json, os, subprocess, sys, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "medir-sessao.py"
FIX = ROOT / "tests" / "fixtures"
CX_REAL = pathlib.Path.home() / ".codex/sessions/2026/09/25/rollout-2026-09-25T03-25-38-01a0d73d-ae04-76b1-a1c3-97d11abc741c.jsonl"
CC_REAL = pathlib.Path.home() / ".claude/projects/-home-nmaldaner-projetos-expedicaosul/e312b9d6-87e3-4a92-b6df-21ec22d88932.jsonl"


def run(*args, check=True):
    r = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True, timeout=600)
    if check:
        assert r.returncode == 0, r.stderr
    return r


def resumo(path):
    return json.loads(run(path, "--json").stdout)


def por_turno(path):
    return json.loads(run(path, "--json", "--por-turno").stdout)


# ---------- Codex (fixture) ----------
def test_codex_fonte_e_linhas():
    r = resumo(FIX / "codex_mini.jsonl")
    assert r["fonte"] == "codex"
    assert r["linhas"] == 12
    assert r["bytes"] == (FIX / "codex_mini.jsonl").stat().st_size


def test_codex_tempo():
    r = resumo(FIX / "codex_mini.jsonl")
    assert r["inicio"] == "2026-09-01T10:00:00.000Z"
    assert r["fim"] == "2026-09-01T11:00:00.000Z"
    assert r["duracao_s"] == 3600


def test_codex_tokens_e_cache():
    r = resumo(FIX / "codex_mini.jsonl")
    assert (r["input_tokens"], r["cached_tokens"], r["cache_write_tokens"], r["output_tokens"]) == (3000, 1800, 0, 120)
    assert r["cache_ratio"] == pytest.approx(0.6)
    assert r["turnos"] == 2


def test_codex_compactacoes_modelos_saida():
    r = resumo(FIX / "codex_mini.jsonl")
    assert r["compactacoes"] == 1
    assert r["modelos"] == ["gpt-6-astra", "gpt-6.1-sol"]
    assert r["bytes_saida_ferramenta"] == 8


def test_codex_por_turno():
    t = por_turno(FIX / "codex_mini.jsonl")
    assert [x["i"] for x in t] == [1, 2]
    assert t[0] == {"i": 1, "timestamp": "2026-09-01T10:00:04.000Z", "input": 1000, "cached": 0, "ratio": 0.0, "compactacoes": 0}
    assert t[1]["input"] == 2000 and t[1]["cached"] == 1800
    assert t[1]["ratio"] == pytest.approx(0.9) and t[1]["compactacoes"] == 1


# ---------- Claude Code (fixture) ----------
def test_claude_fonte_linhas_tempo():
    r = resumo(FIX / "claude_mini.jsonl")
    assert r["fonte"] == "claude"
    assert r["linhas"] == 9
    assert (r["inicio"], r["fim"], r["duracao_s"]) == ("2026-09-02T08:00:00.000Z", "2026-09-02T10:00:00.000Z", 7200)


def test_claude_dedup_por_id_e_cache():
    r = resumo(FIX / "claude_mini.jsonl")
    # msg_1 aparece 2x (blocos de conteúdo): conta uma vez, usage da última ocorrência
    assert r["turnos"] == 2
    assert (r["input_tokens"], r["cached_tokens"], r["cache_write_tokens"], r["output_tokens"]) == (2000, 900, 1085, 55)
    assert r["cache_ratio"] == pytest.approx(0.45)


def test_claude_compactacoes_modelos_saida():
    r = resumo(FIX / "claude_mini.jsonl")
    assert r["compactacoes"] == 1
    assert r["modelos"] == ["claude-opus-5-5", "claude-sonnet-5-5"]
    assert r["bytes_saida_ferramenta"] == 37


def test_claude_por_turno():
    t = por_turno(FIX / "claude_mini.jsonl")
    assert t == [
        {"i": 1, "timestamp": "2026-09-02T08:00:05.000Z", "input": 1000, "cached": 0, "ratio": 0.0, "compactacoes": 0},
        {"i": 2, "timestamp": "2026-09-02T09:00:10.000Z", "input": 1000, "cached": 900, "ratio": 0.9, "compactacoes": 1},
    ]


# ---------- CLI ----------
def test_saida_texto_legivel():
    out = run(FIX / "codex_mini.jsonl").stdout
    assert "codex" in out and "compactações: 1" in out and "cache: 60.0%" in out


def test_arquivo_inexistente_falha_com_mensagem():
    r = run(FIX / "nao-existe.jsonl", check=False)
    assert r.returncode != 0 and "não encontrado" in r.stderr


def test_varios_arquivos_viram_lista():
    out = json.loads(run(FIX / "codex_mini.jsonl", FIX / "claude_mini.jsonl", "--json").stdout)
    assert [x["fonte"] for x in out] == ["codex", "claude"]


# ---------- Sessões reais (oráculo medido em 01/10/2026) ----------
@pytest.mark.real
@pytest.mark.skipif(not CX_REAL.exists(), reason="sessão real ausente")
def test_real_codex_1_8gb():
    r = resumo(CX_REAL)
    assert r["fonte"] == "codex" and r["linhas"] == 10303 and r["compactacoes"] == 13
    assert (r["input_tokens"], r["cached_tokens"], r["output_tokens"]) == (158960699, 155699072, 657950)
    assert r["cache_ratio"] == pytest.approx(155699072 / 158960699)
    assert r["modelos"] == ["gpt-6-astra"] and r["turnos"] == 1367
    assert r["bytes_saida_ferramenta"] == 916212509


@pytest.mark.real
@pytest.mark.skipif(not CC_REAL.exists(), reason="sessão real ausente")
def test_real_claude_17h():
    r = resumo(CC_REAL)
    assert r["fonte"] == "claude" and r["linhas"] == 2469 and r["compactacoes"] == 0
    assert r["duracao_s"] == 63927  # 17h45m27s
    assert (r["turnos"], r["output_tokens"]) == (213, 338702)
    assert r["cache_ratio"] == pytest.approx(0.9814, abs=1e-4)
    assert r["modelos"] == ["claude-opus-5-5"] and r["bytes_saida_ferramenta"] == 23089115

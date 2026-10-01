"""Testes CONGELADOS da F8 (longrun/2026-10-01-recall). O agente não pode alterar esta pasta.

Teste rápido por ciclo:  pytest -q -m "not real" tests/test_recall.py
Teste completo no final: pytest -q
"""
import gzip, json, os, pathlib, shutil, subprocess, sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "recall.py"
FIX = ROOT / "tests" / "fixtures"


@pytest.fixture()
def amb(tmp_path):
    """Pastas falsas de sessões + banco isolado."""
    cx = tmp_path / "codex" / "2026" / "09" / "10"
    cc = tmp_path / "claude" / "-home-u-projetos-gama"
    arq = tmp_path / "arquivo"
    cx.mkdir(parents=True); cc.mkdir(parents=True); arq.mkdir()
    shutil.copy(FIX / "recall_codex.jsonl", cx / "rollout-a.jsonl")
    shutil.copy(FIX / "recall_claude.jsonl", cc / "s1.jsonl")
    env = dict(os.environ, RECALL_DB=str(tmp_path / "recall.db"))
    base = ["--codex", str(tmp_path / "codex"), "--claude", str(tmp_path / "claude"), "--arquivo", str(arq)]

    def run(*args, check=True):
        r = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True, env=env, timeout=300)
        if check:
            assert r.returncode == 0, r.stderr
        return r

    def indexar():
        return run("indexar", *base)

    def buscar(*args):
        return json.loads(run("buscar", *args, "--json").stdout)

    return dict(run=run, indexar=indexar, buscar=buscar, cx=cx, cc=cc, arq=arq, tmp=tmp_path)


def test_busca_basica_codex_sem_duplicar_compactacao(amb):
    amb["indexar"]()
    r = amb["buscar"]("PostgreSQL")
    assert len(r) == 1
    h = r[0]
    assert (h["fonte"], h["projeto"], h["papel"]) == ("codex", "alfa", "user")
    assert h["data"].startswith("2026-09-10")
    assert "PostgreSQL" in h["trecho"]
    assert h["arquivo"].endswith("rollout-a.jsonl") and isinstance(h["linha"], int)


def test_ignora_instrucoes_meta_lembretes_e_pensamento(amb):
    amb["indexar"]()
    assert amb["buscar"]("zebraxyz") == []


def test_ignora_saida_de_ferramenta(amb):
    amb["indexar"]()
    assert amb["buscar"]("quimeraxyz") == []


def test_chamada_de_ferramenta_indexada(amb):
    amb["indexar"]()
    r = amb["buscar"]("alembic")
    assert any(h["papel"] == "ferramenta" for h in r)


def test_projeto_acompanha_mudanca_de_cwd(amb):
    amb["indexar"]()
    r = amb["buscar"]("concluída")
    assert [h["projeto"] for h in r] == ["beta"]


def test_sem_acento_acha_com_acento(amb):
    amb["indexar"]()
    assert len(amb["buscar"]("migracao")) >= 1


def test_claude_texto_lista_e_filtro_papel(amb):
    amb["indexar"]()
    todos = amb["buscar"]("webhook")
    assert {h["fonte"] for h in todos} == {"claude"} and len(todos) >= 2
    so_user = amb["buscar"]("webhook", "--papel", "user")
    assert len(so_user) == 1 and so_user[0]["projeto"] == "gama"
    assert len(amb["buscar"]("certificado")) == 1


def test_filtros_fonte_projeto_desde(amb):
    amb["indexar"]()
    assert all(h["fonte"] == "claude" for h in amb["buscar"]("o", "--fonte", "claude"))
    assert amb["buscar"]("PostgreSQL", "--desde", "2026-09-11") == []
    assert amb["buscar"]("PostgreSQL", "--projeto", "gama") == []
    assert len(amb["buscar"]("PostgreSQL", "--projeto", "alfa")) == 1


def test_incremental_sem_duplicar(amb):
    amb["indexar"]()
    amb["indexar"]()
    assert len(amb["buscar"]("PostgreSQL")) == 1
    with open(amb["cx"] / "rollout-a.jsonl", "a") as f:
        f.write(json.dumps({"timestamp": "2026-09-10T11:00:00.000Z", "type": "response_item",
                            "payload": {"type": "message", "role": "user",
                                        "content": [{"type": "input_text", "text": "agora PostgreSQL de novo"}]}}) + "\n")
    amb["indexar"]()
    assert len(amb["buscar"]("PostgreSQL")) == 2


def test_arquivo_reescrito_menor_reindexa(amb):
    amb["indexar"]()
    p = amb["cx"] / "rollout-a.jsonl"
    linhas = p.read_text().splitlines(keepends=True)
    p.write_text("".join(linhas[:4]))  # só até a pergunta do PostgreSQL
    amb["indexar"]()
    assert len(amb["buscar"]("PostgreSQL")) == 1
    assert amb["buscar"]("Alembic") == []


def test_sessao_arquivada_gz_e_indexada(amb):
    destino = amb["arq"] / "codex" / "2026" / "08" / "01"
    destino.mkdir(parents=True)
    with open(FIX / "recall_codex.jsonl", "rb") as src, gzip.open(destino / "rollout-velho.jsonl.gz", "wb") as dst:
        dst.write(src.read().replace(b"PostgreSQL", b"MariaDB"))
    amb["indexar"]()
    r = amb["buscar"]("MariaDB")
    assert len(r) == 1 and r[0]["fonte"] == "codex" and r[0]["arquivo"].endswith(".gz")


def test_saida_texto_e_atalho_sem_subcomando(amb):
    amb["indexar"]()
    out = amb["run"]("PostgreSQL").stdout
    assert "alfa" in out and "codex" in out and "PostgreSQL" in out


def test_sem_indice_avisa(amb):
    r = amb["run"]("buscar", "qualquer", check=False)
    assert r.returncode != 0 and "indexar" in r.stderr


def test_limite_de_resultados(amb):
    amb["indexar"]()
    assert len(amb["buscar"]("o", "-n", "2")) <= 2


@pytest.mark.real
@pytest.mark.skipif(not (pathlib.Path.home() / ".codex/sessions/2026/10/01").exists(), reason="sessões reais ausentes")
def test_real_acha_frase_do_piloto(tmp_path):
    env = dict(os.environ, RECALL_DB=str(tmp_path / "r.db"))
    vazio = tmp_path / "vazio"; vazio.mkdir()
    base = [sys.executable, str(TOOL)]
    subprocess.run(base + ["indexar", "--codex", str(pathlib.Path.home() / ".codex/sessions/2026/10/01"),
                           "--claude", str(vazio), "--arquivo", str(vazio)], check=True, env=env, capture_output=True, timeout=600)
    r = json.loads(subprocess.run(base + ["buscar", "ler o estado da execução", "--json"], env=env,
                                  capture_output=True, text=True, check=True).stdout)
    assert any(h["projeto"] == "execucao-longa" and h["fonte"] == "codex" for h in r)

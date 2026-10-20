"""Nota de retomada dada pelo script (chaves das perguntas-teste) e causa do erro separada."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTA = ROOT / "tools" / "nota-retomada.py"
GRAVA = pathlib.Path(os.environ.get(
    "HANDOFF_GRAVA", pathlib.Path.home() / ".claude/skills/session-handoff/scripts/handoff-grava.py"))
pytestmark = pytest.mark.skipif(not GRAVA.is_file(), reason="handoff-grava.py não instalado")

PERGUNTAS = """
## Perguntas-teste
1. Qual é a tarefa atual e o critério de pronto? → traduzir o guia — fonte: `tasks/current.md` — chave: `guia/en`
2. Qual foi a última decisão e por quê? → usar Sora nos títulos — fonte: `decisions.md` — chave: `Sora` | `sora-font`
3. O que não pode mudar? → não tocar no v71 — fonte: `CLAUDE.md` — chave: `v71`
4. O que está pela metade? → seção 3 — fonte: `tasks/current.md` — chave: `seção 3`
5. Qual é a próxima ação, por quê, e ela precisa de aprovação? → publicar após OK — fonte: só nesta conversa
"""


def git(raiz, *a):
    return subprocess.run(["git", "-C", str(raiz), *a], capture_output=True, text=True, check=True).stdout


@pytest.fixture
def proj(tmp_path):
    r = tmp_path / "p"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "tasks").mkdir()
    (r / "tasks/current.md").write_text("traduzir guia/en; parou na seção 3\n")
    (r / "decisions.md").write_text("títulos em Sora\n")
    (r / "CLAUDE.md").write_text("não tocar no v71\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    corpo = "# Handoff — teste\n\n" + "linha de estado\n" * 15 + PERGUNTAS
    out = subprocess.run([sys.executable, str(GRAVA), "--raiz", str(r), "--assunto", "t"], input=corpo,
                         capture_output=True, text=True, check=True).stdout
    snap = next(ln.split(": ", 1)[1] for ln in out.splitlines() if ln.startswith("snapshot: "))
    return r, snap, tmp_path / "notas.jsonl"


def nota(notas, *args, entrada=None, ok=True):
    env = {**os.environ, "LONGRUN_NOTAS": str(notas), "HANDOFF_GRAVA": str(GRAVA)}
    r = subprocess.run([sys.executable, str(NOTA), *args], input=entrada, capture_output=True, text=True, env=env)
    if ok:
        assert r.returncode == 0, r.stderr
    return r


def ultimo(notas):
    return json.loads(notas.read_text().splitlines()[-1])


RESP = """1. traduzir o GUIA/EN inteiro
2. decidimos usar a fonte sora
3. não mexer no repo antigo
4. Seção 3 do guia
5. publicar quando o usuário aprovar
"""


def test_script_da_a_nota_pelas_chaves(proj):
    raiz, snap, notas = proj
    r = nota(notas, "--modo", "prime", "--respostas", "-", "--snapshot", snap, "--raiz", str(raiz), entrada=RESP)
    reg = ultimo(notas)
    assert reg["fonte_nota"] == "script"
    assert (reg["acertos"], reg["total"]) == (3, 4)  # a 5 não tem chave: fica fora da conta
    assert [q["resultado"] for q in reg["perguntas"]] == ["certa", "certa", "nao_recuperou", "certa", "nao_conferida"]
    assert reg["perguntas"][2]["resposta"] == "não mexer no repo antigo"  # resposta guardada: dá para auditar
    assert "3/4" in r.stdout and "não conferida" in r.stdout


def test_fonte_mudada_depois_do_handoff_vira_desatualizado(proj):
    raiz, snap, notas = proj
    (raiz / "CLAUDE.md").write_text("v71 liberado; não tocar no v70\n")
    nota(notas, "--modo", "prime", "--respostas", "-", "--snapshot", snap, "--raiz", str(raiz), entrada=RESP)
    reg = ultimo(notas)
    assert reg["perguntas"][2]["resultado"] == "desatualizado"
    assert (reg["acertos"], reg["total"], reg["desatualizadas"], reg["nao_recuperou"]) == (3, 4, 1, 0)


def test_resposta_faltando_conta_como_nao_recuperou(proj):
    raiz, snap, notas = proj
    nota(notas, "--modo", "compactada", "--respostas", "-", "--snapshot", snap, "--raiz", str(raiz),
         entrada="1. guia/en\n")
    reg = ultimo(notas)
    assert reg["acertos"] == 1 and reg["nao_recuperou"] == 3


def test_handoff_sem_chaves_nao_inventa_nota(proj, tmp_path):
    raiz, snap, notas = proj
    p = raiz / snap
    p.write_text(p.read_text().replace(" — chave:", " — x:"))
    r = nota(notas, "--modo", "prime", "--respostas", "-", "--snapshot", snap, "--raiz", str(raiz),
             entrada=RESP, ok=False)
    assert r.returncode != 0 and "chave" in r.stderr and not notas.exists()


def test_relatorio_separa_script_de_autoavaliacao(proj):
    raiz, snap, notas = proj
    (raiz / "CLAUDE.md").write_text("mudou\n")
    nota(notas, "--modo", "prime", "--respostas", "-", "--snapshot", snap, "--raiz", str(raiz), entrada=RESP)
    nota(notas, "--modo", "prime", "--acertos", "5", "--snapshot", snap, "--raiz", str(raiz))
    out = nota(notas, "--relatorio").stdout
    assert "desatualizado" in out and "não recuperou" in out
    linha = next(ln for ln in out.splitlines() if ln.startswith("prime"))
    assert "75%" in linha  # 3/4 do script; a autoavaliada 5/5 não entra na média
    assert "autoavaliadas" in out and "1" in out.split("autoavaliadas", 1)[1]

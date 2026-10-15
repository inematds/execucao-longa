"""Testes do hook-longrun: faixas sobre o teto, handoff conferido, compactações, pausa e /clear."""
import json, os, pathlib, subprocess, sys, time, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "tools" / "hook-longrun.py"


def iso(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def assistente(tokens, quando=None, model="claude-opus-5-5"):
    return {"type": "assistant", "timestamp": iso(quando or time.time()),
            "message": {"model": model, "content": [{"type": "text", "text": "ok"}],
                        "usage": {"input_tokens": 10, "cache_read_input_tokens": tokens - 10, "cache_creation_input_tokens": 0}}}


def escrita(rel, quando=None):
    return {"type": "assistant", "timestamp": iso(quando or time.time()),
            "message": {"model": "claude-opus-5-5", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": f"/x/{rel}", "content": "..."}}]}}


class Ambiente:
    def __init__(self, tmp, handoffs=True):
        self.proj = tmp / "proj"
        self.proj.mkdir()
        if handoffs:
            (self.proj / "handoffs" / "history").mkdir(parents=True)
        self.estado = tmp / "estado"
        self.tr = tmp / "t.jsonl"
        self.tr.write_text("")

    def linhas(self, *regs):
        with open(self.tr, "a") as f:
            for r in regs:
                f.write(json.dumps(r) + "\n")

    def run(self, ev, **extra):
        d = {"hook_event_name": ev, "cwd": str(self.proj), "session_id": "s1", "transcript_path": str(self.tr), **extra}
        env = {**os.environ, "LONGRUN_ESTADO": str(self.estado)}
        env.pop("LONGRUN_JANELA", None)
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(d), capture_output=True, text=True, env=env, timeout=30)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout) if r.stdout.strip() else {}


def ctx(out):
    return (out.get("hookSpecificOutput") or {}).get("additionalContext", "")


def test_faixa2_dispara_sobre_o_ponto_de_compactacao(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(730_000))  # 75% do ponto de compactação (~967 mil); com o teto antigo de 225 mil seria 324%
    out = a.run("PostToolUse")
    assert "grave o handoff AGORA" in ctx(out)
    assert a.run("PostToolUse") == {}  # uma vez por faixa


def test_abaixo_da_faixa_nao_avisa(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(520_000))
    assert a.run("PostToolUse") == {}


def test_handoff_conferido(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(730_000))
    a.run("PostToolUse")
    rel = "handoffs/history/2026-10-15T050000Z.md"
    (a.proj / rel).write_text("x" * 300)
    a.linhas(escrita(rel))
    out = a.run("PostToolUse")
    assert "Handoff conferido" in out.get("systemMessage", "")


def test_handoff_pelo_script_conferido(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(730_000))
    a.run("PostToolUse")
    (a.proj / "handoffs/history/2026-10-15T050000Z-x.md").write_text("x" * 300)
    a.linhas({"type": "assistant", "timestamp": iso(time.time()), "message": {"model": "claude-opus-5-5", "content": [
        {"type": "tool_use", "name": "Bash",
         "input": {"command": "python3 ~/.claude/skills/session-handoff/scripts/handoff-grava.py --assunto x <<EOF"}}]}})
    assert "Handoff conferido" in a.run("PostToolUse").get("systemMessage", "")


def test_handoff_vazio_nao_conta(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(730_000))
    a.run("PostToolUse")
    rel = "handoffs/history/2026-10-15T050000Z.md"
    (a.proj / rel).write_text("curto")
    a.linhas(escrita(rel))
    assert "conferido" not in a.run("PostToolUse").get("systemMessage", "")


def test_cobra_e_depois_desiste(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(730_000))
    a.run("PostToolUse")
    saidas = [a.run("PostToolUse") for _ in range(30)]
    cobrancas = [o for o in saidas if "AINDA NÃO FOI GRAVADO" in ctx(o)]
    desistiu = [o for o in saidas if "NÃO foi gravado" in o.get("systemMessage", "")]
    assert len(cobrancas) == 2 and len(desistiu) == 1


def test_sem_pasta_handoffs_nao_cobra(tmp_path):
    a = Ambiente(tmp_path, handoffs=False)
    a.linhas(assistente(730_000))
    a.run("PostToolUse")
    assert all(a.run("PostToolUse") == {} for _ in range(20))


def test_terceira_compactacao_pede_sessao_nova(tmp_path):
    a = Ambiente(tmp_path)
    outs = [a.run("SessionStart", source="compact") for _ in range(3)]
    assert "sessão nova" not in ctx(outs[1])
    assert "3ª compactação" in ctx(outs[2]) and "/clear" in outs[2].get("systemMessage", "")


def test_pausa_bloqueia_uma_vez(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(200_000, quando=time.time() - 2 * 3600))
    out = a.run("UserPromptSubmit", prompt="oi")
    assert out.get("decision") == "block" and "cache venceu" in out["reason"]
    assert a.run("UserPromptSubmit", prompt="oi").get("decision") is None  # reenviar passa


def test_pausa_curta_ou_contexto_pequeno_nao_bloqueia(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(200_000, quando=time.time() - 20 * 60))
    assert a.run("UserPromptSubmit", prompt="oi").get("decision") is None
    (tmp_path / "b").mkdir()
    b = Ambiente(tmp_path / "b")
    b.linhas(assistente(90_000, quando=time.time() - 3 * 3600))
    assert b.run("UserPromptSubmit", prompt="oi").get("decision") is None


def test_clear_aponta_ultimo_handoff(tmp_path):
    a = Ambiente(tmp_path)
    (a.proj / "handoffs/history/2026-10-15T010000Z.md").write_text("a" * 300)
    out = a.run("SessionStart", source="clear")
    assert "handoffs/history/2026-10-15T010000Z.md" in ctx(out)


def test_clear_lista_indice_de_abertos(tmp_path):
    a = Ambiente(tmp_path)
    h = a.proj / "handoffs/history"
    (h / "2026-10-15T010000Z-rea-es.md").write_text("a" * 300)
    (h / "2026-10-15T020000Z-cerebro.md").write_text("b" * 300)
    (a.proj / "handoffs/latest.md").write_text(
        "# Handoffs\n\n<!-- handoff-indice:inicio -->\n"
        "- `cerebro` · handoffs/history/2026-10-15T020000Z-cerebro.md · 15/10 02:00\n"
        "- `rea-es` · handoffs/history/2026-10-15T010000Z-rea-es.md · 15/10 01:00\n"
        "<!-- handoff-indice:fim -->\n")
    c = ctx(a.run("SessionStart", source="clear"))
    assert "cerebro → handoffs/history/2026-10-15T020000Z-cerebro.md" in c and "rea-es →" in c


def test_clear_usa_indice_txt_se_latest_foi_sobrescrito(tmp_path):
    a = Ambiente(tmp_path)
    (a.proj / "handoffs/history/2026-10-15T010000Z-rea-es.md").write_text("a" * 300)
    (a.proj / "handoffs/latest.md").write_text("# Handoff antigo\n" + "x" * 300)
    (a.proj / "handoffs/indice.txt").write_text(
        "- `rea-es` · handoffs/history/2026-10-15T010000Z-rea-es.md · 15/10 01:00\n")
    assert "rea-es → handoffs/history/2026-10-15T010000Z-rea-es.md" in ctx(a.run("SessionStart", source="clear"))


def test_clear_avisa_carimbo_inventado_so_no_futuro(tmp_path):
    a = Ambiente(tmp_path)
    h = a.proj / "handoffs/history"
    futuro = h / "2099-01-01T120000Z-x.md"
    futuro.write_text("a" * 300)
    velho = h / "2001-01-01T000000Z-y.md"  # clone renova o mtime: nome antigo é normal
    velho.write_text("a" * 300)
    c = ctx(a.run("SessionStart", source="clear"))
    assert "inventado" in c and futuro.name in c and velho.name not in c.split("inventado")[1]


def test_estado_antigo_numero_puro(tmp_path):
    a = Ambiente(tmp_path)
    a.estado.mkdir()
    (a.estado / "s1").write_text("2")
    a.linhas(assistente(730_000))
    assert a.run("PostToolUse") == {}  # já estava na faixa 2


def test_continuo_pede_uma_vez_e_respeita_intervalo(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(260_000))
    out = a.run("Stop")
    assert out.get("decision") == "block" and "Handoff contínuo" in out["reason"]
    assert a.run("Stop") == {}  # 1 pedido a cada 30 min


def test_continuo_nao_repete_quando_o_stop_ja_fez_continuar(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(260_000))
    assert a.run("Stop", stop_hook_active=True) == {}


def test_continuo_pula_com_handoff_recente_ou_contexto_pequeno(tmp_path):
    a = Ambiente(tmp_path)
    rel = "handoffs/history/2026-10-15T060000Z.md"
    (a.proj / rel).write_text("x" * 300)
    a.linhas(assistente(260_000), escrita(rel))
    assert a.run("Stop") == {}
    (tmp_path / "b").mkdir()
    b = Ambiente(tmp_path / "b")
    b.linhas(assistente(100_000))
    assert b.run("Stop") == {}
    (tmp_path / "c").mkdir()
    c = Ambiente(tmp_path / "c", handoffs=False)
    c.linhas(assistente(260_000))
    assert c.run("Stop") == {}


def test_continuo_depois_confere_o_handoff(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(255_000))
    a.run("Stop")
    rel = "handoffs/history/2026-10-15T070000Z.md"
    (a.proj / rel).write_text("x" * 300)
    a.linhas(escrita(rel))
    assert "Handoff conferido" in a.run("PostToolUse").get("systemMessage", "")


def test_longrun_faixa1_no_teto(tmp_path):
    a = Ambiente(tmp_path)
    lr = a.proj / "longrun" / "x"
    lr.mkdir(parents=True)
    (lr / "state.md").write_text("em andamento")
    a.linhas(assistente(520_000))
    assert "FAIXA 1 de 3" in ctx(a.run("PostToolUse"))


def test_faixa3_nao_manda_parar_a_tarefa(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(860_000))
    texto = ctx(a.run("PostToolUse"))
    assert "CONTINUE a tarefa" in texto and "Não abra trabalho novo" not in texto
    assert texto.count("Depois avise") == 1


def test_teto_antigo_nao_dispara_mais(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(200_000))  # 21%: em 1.2.x virava faixa 3 (89% de 225 mil)
    assert a.run("PostToolUse") == {}


def test_pos_compactacao_com_handoff_recente_nao_cobra(tmp_path):
    a = Ambiente(tmp_path)
    rel = "handoffs/history/2026-10-15T080000Z.md"
    (a.proj / rel).write_text("x" * 300)
    a.linhas(assistente(30_000), escrita(rel))
    out = a.run("SessionStart", source="compact")
    assert "releia" in ctx(out)
    assert all("AINDA NÃO FOI GRAVADO" not in ctx(a.run("PostToolUse")) for _ in range(12))

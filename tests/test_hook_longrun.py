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
        self.env = {"LONGRUN_AGENDAR_ARQ": str(tmp / "agenda.jsonl")}

    def linhas(self, *regs):
        with open(self.tr, "a") as f:
            for r in regs:
                f.write(json.dumps(r) + "\n")

    def run(self, ev, **extra):
        d = {"hook_event_name": ev, "cwd": str(self.proj), "session_id": "s1", "transcript_path": str(self.tr), **extra}
        env = {**os.environ, "LONGRUN_ESTADO": str(self.estado), **self.env}
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
    a.env["LONGRUN_CONTINUO_TOKENS"] = "200000"  # modo antigo, desligado por padrão desde 1.5.1
    a.linhas(assistente(260_000))
    out = a.run("Stop")
    assert out.get("decision") == "block" and "Handoff contínuo" in out["reason"]
    assert a.run("Stop") == {}  # 1 pedido a cada 30 min


def test_continuo_nao_repete_quando_o_stop_ja_fez_continuar(tmp_path):
    a = Ambiente(tmp_path)
    a.env["LONGRUN_CONTINUO_TOKENS"] = "200000"  # modo antigo, desligado por padrão desde 1.5.1
    a.linhas(assistente(260_000))
    assert a.run("Stop", stop_hook_active=True) == {}


def test_continuo_pula_com_handoff_recente_ou_contexto_pequeno(tmp_path):
    a = Ambiente(tmp_path)
    a.env["LONGRUN_CONTINUO_TOKENS"] = "200000"  # modo antigo, desligado por padrão desde 1.5.1
    rel = "handoffs/history/2026-10-15T060000Z.md"
    (a.proj / rel).write_text("x" * 300)
    a.linhas(assistente(260_000), escrita(rel))
    assert a.run("Stop") == {}
    (tmp_path / "b").mkdir()
    b = Ambiente(tmp_path / "b")
    b.env["LONGRUN_CONTINUO_TOKENS"] = "200000"
    b.linhas(assistente(100_000))
    assert b.run("Stop") == {}
    (tmp_path / "c").mkdir()
    c = Ambiente(tmp_path / "c", handoffs=False)
    c.env["LONGRUN_CONTINUO_TOKENS"] = "200000"
    c.linhas(assistente(260_000))
    assert c.run("Stop") == {}


def test_continuo_depois_confere_o_handoff(tmp_path):
    a = Ambiente(tmp_path)
    a.env["LONGRUN_CONTINUO_TOKENS"] = "200000"  # modo antigo, desligado por padrão desde 1.5.1
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


# ---------- 1.5.1: handoff por ociosidade (agenda no Stop, grava numa cópia da sessão se ficar parada) ----------
import importlib.util

_spec = importlib.util.spec_from_file_location("hook", HOOK)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def agenda(tmp_path):
    arq = tmp_path / "agenda.jsonl"
    return [json.loads(l) for l in arq.read_text().splitlines()] if arq.exists() else []


def test_stop_nao_interrompe_mais_quem_trabalha(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(285_000))
    assert a.run("Stop") == {}  # sem "block": o pedido no meio do trabalho acabou
    [ag] = agenda(tmp_path)
    assert ag["minutos"] == 30 and ag["unidade"].startswith("longrun-ocioso-") and "--ocioso" in ag["cmd"]


def test_stop_nao_agenda_com_contexto_pequeno_sem_handoffs_ou_na_copia(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(120_000))
    a.run("Stop")
    (tmp_path / "b").mkdir()
    b = Ambiente(tmp_path / "b", handoffs=False)
    b.linhas(assistente(285_000))
    b.run("Stop")
    (tmp_path / "c").mkdir()
    c = Ambiente(tmp_path / "c")
    c.env["LONGRUN_HEADLESS"] = "1"  # a própria cópia não agenda outra
    c.linhas(assistente(285_000))
    c.run("Stop")
    assert agenda(tmp_path) == [] and agenda(tmp_path / "b") == [] and agenda(tmp_path / "c") == []


def test_decidir_ocioso():
    t0 = 1_000_000.0
    agora = t0 + 30 * 60
    assert hook.decidir_ocioso(agora, t0, t0 + 10, 300_000, 200_000, False)[0] is True
    assert "andou" in hook.decidir_ocioso(agora, t0, t0 + 600, 300_000, 200_000, False)[1]
    assert "venceu" in hook.decidir_ocioso(t0 + 56 * 60, t0, t0, 300_000, 200_000, False)[1]
    assert "pequeno" in hook.decidir_ocioso(agora, t0, t0, 150_000, 200_000, False)[1]
    assert "recente" in hook.decidir_ocioso(agora, t0, t0, 300_000, 200_000, True)[1]


def _rodar_ocioso(a, tmp_path, ultimo_stop, stub):
    env = {**os.environ, "LONGRUN_ESTADO": str(a.estado), "LONGRUN_CLAUDE_CMD": f"{sys.executable} {stub}", "HOME": str(tmp_path)}
    r = subprocess.run([sys.executable, str(HOOK), "--ocioso", "s1", str(a.tr), str(a.proj), str(ultimo_stop)],
                       capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0, r.stderr


def _stub(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text("import pathlib,sys,time\nsys.stdin.read()\n"
                    "p=pathlib.Path('handoffs/history')/time.strftime('%Y-%m-%dT%H%M%SZ-x.md');p.write_text('x'*300)\n"
                    "print('Handoff atualizado:',p)\n")
    return stub


def test_ocioso_grava_na_copia_e_registra(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(285_000, quando=time.time() - 31 * 60))
    parado = time.time() - 31 * 60
    os.utime(a.tr, (parado, parado))
    a.run("Stop")  # registra ultimo_stop agora; o teste usa o valor gravado
    st = json.loads(next(a.estado.iterdir()).read_text())
    os.utime(a.tr, (st["ultimo_stop"] - 5, st["ultimo_stop"] - 5))
    _rodar_ocioso(a, tmp_path, st["ultimo_stop"], _stub(tmp_path))
    st = json.loads(next(a.estado.iterdir()).read_text())
    assert st["handoff_ocioso"]["arquivo"].startswith("handoffs/history/")


def test_ocioso_nao_grava_se_a_sessao_andou_ou_agendamento_velho(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(285_000))
    a.run("Stop")
    st = json.loads(next(a.estado.iterdir()).read_text())
    stub = _stub(tmp_path)
    os.utime(a.tr, (st["ultimo_stop"] + 600, st["ultimo_stop"] + 600))  # mexeu depois do Stop
    _rodar_ocioso(a, tmp_path, st["ultimo_stop"], stub)
    os.utime(a.tr, (st["ultimo_stop"], st["ultimo_stop"]))
    _rodar_ocioso(a, tmp_path, st["ultimo_stop"] - 100, stub)  # um Stop mais novo já reagendou
    assert list((a.proj / "handoffs" / "history").iterdir()) == []


# --- 1.6.1: medição de retomada (perguntas-teste de memória × /prime) ---

NOTA = ROOT / "tools" / "nota-retomada.py"
SNAP_PT = "# Handoff\n\n## Perguntas-teste\n1. Qual é a tarefa atual? → x — fonte: `a.md`\n" + "linha\n" * 40


def com_perguntas(a, nome="2026-10-17T010000Z-x.md"):
    (a.proj / "handoffs/history" / nome).write_text(SNAP_PT)
    return f"handoffs/history/{nome}"


def test_compactacao_pede_respostas_de_memoria_antes_do_handoff(tmp_path):
    a = Ambiente(tmp_path)
    rel = com_perguntas(a)
    texto = ctx(a.run("SessionStart", source="compact"))
    assert "MEDIÇÃO DE RETOMADA (modo compactada)" in texto
    assert "de memória" in texto and "O que está pela metade?" in texto
    assert rel in texto and "nota-retomada.py" in texto and "--modo compactada" in texto
    assert texto.index("MEDIÇÃO") < texto.index("releia")  # mede antes de reler


def test_sem_secao_perguntas_nao_mede(tmp_path):
    a = Ambiente(tmp_path)
    (a.proj / "handoffs/history/2026-10-17T010000Z-x.md").write_text("# Handoff antigo\n" + "l\n" * 40)
    assert "MEDIÇÃO" not in ctx(a.run("SessionStart", source="compact"))


def test_resume_mede_como_retomada(tmp_path):
    a = Ambiente(tmp_path)
    com_perguntas(a)
    a.linhas(assistente(300_000))
    assert "(modo retomada)" in ctx(a.run("SessionStart", source="resume"))


def test_volta_da_pausa_mede_uma_vez_como_continuada(tmp_path):
    a = Ambiente(tmp_path)
    com_perguntas(a)
    a.linhas(assistente(200_000, quando=time.time() - 2 * 3600))
    assert a.run("UserPromptSubmit", prompt="oi").get("decision") == "block"
    texto = ctx(a.run("UserPromptSubmit", prompt="oi"))
    assert "(modo continuada)" in texto and "--tokens 200000" in texto
    assert "MEDIÇÃO" not in ctx(a.run("UserPromptSubmit", prompt="oi"))


def test_clear_pede_nota_do_prime(tmp_path):
    a = Ambiente(tmp_path)
    com_perguntas(a)
    texto = ctx(a.run("SessionStart", source="clear"))
    assert "--modo prime" in texto and "nota-retomada.py" in texto


def test_medir_desligado(tmp_path):
    a = Ambiente(tmp_path)
    com_perguntas(a)
    a.env["LONGRUN_MEDIR"] = "0"
    assert "MEDIÇÃO" not in ctx(a.run("SessionStart", source="compact"))
    assert "--modo prime" not in ctx(a.run("SessionStart", source="clear"))


def test_nota_retomada_registra_e_relata(tmp_path):
    env = {**os.environ, "LONGRUN_NOTAS": str(tmp_path / "notas.jsonl")}
    def nota(*args):
        r = subprocess.run([sys.executable, str(NOTA), *args], capture_output=True, text=True, env=env)
        assert r.returncode == 0, r.stderr
        return r.stdout
    nota("--modo", "compactada", "--acertos", "3", "--snapshot", "handoffs/history/x.md", "--raiz", "/p", "--tokens", "250000")
    nota("--modo", "compactada", "--acertos", "5", "--snapshot", "handoffs/history/x.md", "--raiz", "/p")
    nota("--modo", "prime", "--acertos", "4", "--snapshot", "handoffs/history/x.md", "--raiz", "/p")
    linhas = (tmp_path / "notas.jsonl").read_text().splitlines()
    assert len(linhas) == 3 and json.loads(linhas[0])["acertos"] == 3
    rel = nota("--relatorio")
    assert "compactada" in rel and "80%" in rel and "prime" in rel
    r = subprocess.run([sys.executable, str(NOTA), "--modo", "x", "--acertos", "9"], capture_output=True, text=True, env=env)
    assert r.returncode != 0


def resultado_grava(rel, quando=None):
    return {"type": "user", "timestamp": iso(quando or time.time()),
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "x", "content": f"snapshot: {rel}\nlatest.md: 2 assunto(s)"}]}}


def test_pausa_aponta_o_handoff_desta_sessao_e_nao_o_mais_novo(tmp_path):
    a = Ambiente(tmp_path)
    hist = a.proj / "handoffs" / "history"
    meu, outro = "2026-10-17T100000Z-robot.md", "2026-10-17T110000Z-outro.md"
    (hist / meu).write_text("x" * 300)
    (hist / outro).write_text("x" * 300)  # gravado depois por outra sessão
    a.linhas(resultado_grava(f"handoffs/history/{meu}", quando=time.time() - 2 * 3600 - 60),
             assistente(200_000, quando=time.time() - 2 * 3600))
    out = a.run("UserPromptSubmit", prompt="oi")
    assert out.get("decision") == "block"
    assert f"/prime handoffs/history/{meu}" in out["reason"] and outro not in out["reason"]


def test_pausa_sem_handoff_da_sessao_mantem_prime_simples(tmp_path):
    a = Ambiente(tmp_path)
    a.linhas(assistente(200_000, quando=time.time() - 2 * 3600))
    out = a.run("UserPromptSubmit", prompt="oi")
    assert "/prime handoffs/history/" not in out["reason"]

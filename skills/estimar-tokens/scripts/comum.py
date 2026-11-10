"""Funções compartilhadas pelos scripts do estimar-tokens: preços e registros."""

import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PASTA_USUARIO = Path.home() / ".claude" / "estimar-tokens"
PROJETOS = Path.home() / ".claude" / "projects"
AVISO_USD = (
    "Valores em US$ pelo preço da API Anthropic. Para assinantes do Claude.ai, "
    "é o equivalente em API, não uma cobrança."
)


def carregar_precos():
    """Tabela padrão, sobrescrita por ~/.claude/estimar-tokens/precos.json se existir."""
    precos = json.loads((AQUI.parent / "references" / "precos.json").read_text(encoding="utf-8"))
    extra = PASTA_USUARIO / "precos.json"
    if extra.exists():
        outro = json.loads(extra.read_text(encoding="utf-8"))
        precos["modelos"].update(outro.get("modelos", {}))
        for k in ("multiplicador_escrita_5m", "multiplicador_escrita_1h"):
            precos[k] = outro.get(k, precos[k])
    return precos


def preco_modelo(precos, modelo):
    """Preço do modelo; aceita IDs com sufixo de data (claude-haiku-4-5-20251001)."""
    tabela = precos["modelos"]
    if modelo in tabela:
        return tabela[modelo]
    candidatos = [m for m in tabela if modelo and modelo.startswith(m)]
    return tabela[max(candidatos, key=len)] if candidatos else None


def custo_usd(precos, modelo, entrada=0, escrita_5m=0, escrita_1h=0, leitura=0, saida=0):
    p = preco_modelo(precos, modelo)
    if p is None:
        return None
    mtok = 1_000_000
    return (
        entrada * p["entrada"]
        + escrita_5m * p["entrada"] * precos["multiplicador_escrita_5m"]
        + escrita_1h * p["entrada"] * precos["multiplicador_escrita_1h"]
        + leitura * p["leitura_cache"]
        + saida * p["saida"]
    ) / mtok


def uso_detalhado(uso):
    """Separa o usage de uma resposta em entrada, escritas 5m/1h, leitura e saída."""
    cc = uso.get("cache_creation") or {}
    e5 = cc.get("ephemeral_5m_input_tokens")
    e1 = cc.get("ephemeral_1h_input_tokens")
    total_escrita = uso.get("cache_creation_input_tokens", 0) or 0
    if e5 is None and e1 is None:
        e5, e1 = total_escrita, 0
    return {
        "entrada": uso.get("input_tokens", 0) or 0,
        "escrita_5m": e5 or 0,
        "escrita_1h": e1 or 0,
        "leitura": uso.get("cache_read_input_tokens", 0) or 0,
        "saida": uso.get("output_tokens", 0) or 0,
    }


def respostas_com_modelo(arquivo, desde=None):
    """Respostas do assistente (id, modelo, usage, timestamp), sem duplicar pedaços da mesma mensagem."""
    por_id = {}
    with open(arquivo, encoding="utf-8", errors="replace") as f:
        for linha in f:
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            if d.get("type") != "assistant":
                continue
            m = d.get("message") or {}
            if not m.get("usage") or not m.get("id") or m.get("model") == "<synthetic>":
                continue
            ts = d.get("timestamp", "")
            if desde and ts and ts < desde:
                continue
            por_id[m["id"]] = {"modelo": m.get("model"), "uso": m["usage"], "ts": ts}
    return list(por_id.values())


def sessao_atual():
    """ID da sessão gravado pela status line ou, sem ele, o registro mais recente."""
    try:
        sid = json.loads((PASTA_USUARIO / "saldo.json").read_text()).get("sessao")
        if sid:
            return sid
    except (OSError, ValueError):
        pass
    arquivos = sorted(PROJETOS.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime)
    return arquivos[-1].stem if arquivos else None


def arquivos_da_sessao(sid):
    """Registro principal da sessão e os dos subagentes dela."""
    principal = list(PROJETOS.glob(f"*/{sid}.jsonl"))
    subagentes = list(PROJETOS.glob(f"*/{sid}/subagents/*.jsonl"))
    return principal, subagentes


def contexto_atual():
    try:
        return json.loads((PASTA_USUARIO / "saldo.json").read_text()).get("contexto_tokens")
    except (OSError, ValueError):
        return None


def modelo_recente():
    sid = sessao_atual()
    if sid:
        principal, _ = arquivos_da_sessao(sid)
        for arq in principal:
            rs = respostas_com_modelo(arq)
            if rs:
                return rs[-1]["modelo"]
    return "claude-opus-5-5"


def usd(v):
    return "—" if v is None else f"US$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mil(n):
    return f"{n / 1000:,.1f} mil".replace(",", "X").replace(".", ",").replace("X", ".")

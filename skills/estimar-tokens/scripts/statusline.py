#!/usr/bin/env python3
"""Status line do Claude Code que mostra o saldo e o grava para a skill estimar-tokens.

O Claude Code envia à status line, pela entrada padrão, um JSON com o uso do
contexto e, para assinantes, o percentual usado dos limites de 5 horas e de
7 dias. Este script grava esse retrato em ~/.claude/estimar-tokens/saldo.json
e imprime as barras de uso. Numa segunda linha, mostra os tokens e o custo em
US$ da sessão, com os subagentes, somados a partir do registro da sessão.

Configure em ~/.claude/settings.json:
    "statusLine": {"type": "command", "command": "python3 /caminho/statusline.py"}

Para manter uma status line que você já usa, passe o comando dela em
--encadear; a saída dela vem antes do saldo:
    "command": "python3 /caminho/statusline.py --encadear 'bash ~/minha-statusline.sh'"
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

SALDO = comum.PASTA_USUARIO / "saldo.json"
SESSOES = comum.PASTA_USUARIO / "sessoes"
VALIDADE_CACHE = 30 * 86400
LARGURA_BARRA = 8
OITAVOS = " ▏▎▍▌▋▊▉"


def barra(pct):
    """Barra horizontal de LARGURA_BARRA caracteres, com resolução de 1/8 de caractere."""
    oitavos = round(max(0, min(100, pct)) / 100 * LARGURA_BARRA * 8)
    cheios, resto = divmod(oitavos, 8)
    texto = "█" * cheios + (OITAVOS[resto] if resto else "")
    return texto + "░" * (LARGURA_BARRA - len(texto))


def gravar(dados, destino=SALDO):
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=destino.parent)
    with os.fdopen(fd, "w") as f:
        json.dump(dados, f)
    os.replace(tmp, destino)


def ler_novas(arquivo, estado):
    """Lê só as linhas completas acrescentadas desde a última vez e guarda o usage de cada mensagem."""
    if arquivo.stat().st_size < estado["pos"]:  # arquivo reescrito
        estado.update(pos=0, msgs={})
    with open(arquivo, "rb") as f:
        f.seek(estado["pos"])
        for linha in f:
            if not linha.endswith(b"\n"):
                break
            estado["pos"] += len(linha)
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            if d.get("type") != "assistant":
                continue
            m = d.get("message") or {}
            if m.get("usage") and m.get("id") and m.get("model") != "<synthetic>":
                estado["msgs"][m["id"]] = [m.get("model"), comum.uso_detalhado(m["usage"])]


def total_sessao(transcript):
    """Tokens e US$ da sessão e dos subagentes dela, com cache incremental por sessão."""
    principal = Path(transcript)
    arquivos = [principal] + sorted(principal.with_suffix("").glob("subagents/*.jsonl"))
    destino = SESSOES / f"{principal.stem}.json"
    try:
        cache = json.loads(destino.read_text())
    except (OSError, ValueError):
        cache = {}
        for velho in SESSOES.glob("*.json"):
            if time.time() - velho.stat().st_mtime > VALIDADE_CACHE:
                velho.unlink(missing_ok=True)
    for arq in arquivos:
        ler_novas(arq, cache.setdefault(str(arq), {"pos": 0, "msgs": {}}))
    gravar(cache, destino)

    precos = comum.carregar_precos()
    tokens = novos = 0
    valor = 0.0
    for estado in cache.values():
        for modelo, u in estado["msgs"].values():
            tokens += sum(u.values())
            novos += sum(u.values()) - u["leitura"]
            valor += comum.custo_usd(precos, modelo, **u) or 0
    return tokens, novos, valor


def qtd(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} mi".replace(".", ",")
    return comum.mil(n)


def main():
    bruto = sys.stdin.read()
    try:
        entrada = json.loads(bruto)
    except ValueError:
        entrada = {}

    ctx = entrada.get("context_window") or {}
    limites = entrada.get("rate_limits") or {}
    retrato = {
        "gravado_em": int(time.time()),
        "sessao": entrada.get("session_id"),
        "contexto_tokens": ctx.get("total_input_tokens"),
        "contexto_pct": ctx.get("used_percentage"),
        "contexto_tamanho": ctx.get("context_window_size"),
        "limites": {
            nome: {"usado_pct": v.get("used_percentage"), "renova_em": v.get("resets_at")}
            for nome, v in limites.items()
            if isinstance(v, dict)
        },
    }
    try:
        gravar(retrato)
    except OSError:
        pass

    partes = []
    if "--encadear" in sys.argv:
        cmd = sys.argv[sys.argv.index("--encadear") + 1]
        try:
            r = subprocess.run(cmd, shell=True, input=bruto, capture_output=True, text=True, timeout=5)
            if r.stdout.strip():
                partes.append(r.stdout.rstrip("\n"))
        except (subprocess.SubprocessError, OSError):
            pass

    rotulos = {"five_hour": "5h", "seven_day": "7d", "spend_limit": "gasto"}
    saldo = [
        f"{rotulos.get(nome, nome)} {barra(v['usado_pct'])} {v['usado_pct']:.0f}%"
        for nome, v in retrato["limites"].items()
        if v.get("usado_pct") is not None
    ]
    if retrato["contexto_pct"] is not None:
        saldo.append(f"ctx {barra(retrato['contexto_pct'])} {retrato['contexto_pct']:.0f}%")
    if saldo:
        partes.append(" · ".join(saldo))
    linhas = [" | ".join(partes)]

    if entrada.get("transcript_path"):
        try:
            tokens, novos, valor = total_sessao(entrada["transcript_path"])
            if tokens:
                linhas.append(f"sessão {qtd(tokens)} tokens ({qtd(novos)} novos) · {comum.usd(valor)}")
        except (OSError, ValueError, KeyError, TypeError):
            pass
    print("\n".join(linhas))


if __name__ == "__main__":
    main()

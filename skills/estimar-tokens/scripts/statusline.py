#!/usr/bin/env python3
"""Status line do Claude Code que mostra o saldo e o grava para a skill estimar-tokens.

O Claude Code envia à status line, pela entrada padrão, um JSON com o uso do
contexto e, para assinantes, o percentual usado dos limites de 5 horas e de
7 dias. Este script grava esse retrato em ~/.claude/estimar-tokens/saldo.json
e imprime uma linha curta.

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

SALDO = Path.home() / ".claude" / "estimar-tokens" / "saldo.json"
LARGURA_BARRA = 8
OITAVOS = " ▏▎▍▌▋▊▉"


def barra(pct):
    """Barra horizontal de LARGURA_BARRA caracteres, com resolução de 1/8 de caractere."""
    oitavos = round(max(0, min(100, pct)) / 100 * LARGURA_BARRA * 8)
    cheios, resto = divmod(oitavos, 8)
    texto = "█" * cheios + (OITAVOS[resto] if resto else "")
    return texto + "░" * (LARGURA_BARRA - len(texto))


def gravar(dados):
    SALDO.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=SALDO.parent)
    with os.fdopen(fd, "w") as f:
        json.dump(dados, f)
    os.replace(tmp, SALDO)


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
    print(" | ".join(partes))


if __name__ == "__main__":
    main()

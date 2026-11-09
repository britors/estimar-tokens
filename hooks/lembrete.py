#!/usr/bin/env python3
"""Lembra o Claude de estimar tokens a cada pedido, com o saldo atual.

Desligado por padrão: só age se ~/.claude/estimar-tokens/lembrete existir.
Ligar:    touch ~/.claude/estimar-tokens/lembrete
Desligar: rm ~/.claude/estimar-tokens/lembrete
O texto impresso entra no contexto do pedido (cerca de 60 tokens).
"""

import json
import time
from pathlib import Path

PASTA = Path.home() / ".claude" / "estimar-tokens"


def main():
    if not (PASTA / "lembrete").exists():
        return
    saldo = ""
    try:
        r = json.loads((PASTA / "saldo.json").read_text())
        if time.time() - r.get("gravado_em", 0) < 600:
            partes = [
                f"{n} {v['usado_pct']:.0f}% usado"
                for n, v in (r.get("limites") or {}).items()
                if v.get("usado_pct") is not None
            ]
            if r.get("contexto_tokens"):
                partes.append(f"contexto {r['contexto_tokens'] / 1000:.0f} mil")
            if partes:
                saldo = " Saldo: " + ", ".join(partes) + "."
    except (OSError, ValueError, KeyError, TypeError):
        pass
    print("[estimar-tokens] Antes de agir, siga a skill estimar-tokens: estime cada etapa e avise o custo." + saldo)


if __name__ == "__main__":
    main()

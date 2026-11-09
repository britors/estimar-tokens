#!/usr/bin/env python3
"""Mostra o último saldo gravado pela status line do estimar-tokens.

Sai com código 2 quando não há retrato (status line não configurada) e com 1
quando o retrato tem mais de 10 minutos.
"""

import json
import sys
import time
from pathlib import Path

SALDO = Path.home() / ".claude" / "estimar-tokens" / "saldo.json"
VELHO = 600
NOMES = {"five_hour": "limite de 5 horas", "seven_day": "limite de 7 dias", "spend_limit": "limite de gasto"}


def main():
    try:
        r = json.loads(SALDO.read_text())
    except (OSError, ValueError):
        print("Sem saldo gravado: configure scripts/statusline.py como status line (veja o README).")
        sys.exit(2)

    idade = int(time.time() - r.get("gravado_em", 0))
    print(f"Retrato de {idade // 60} min atrás.")
    for nome, v in (r.get("limites") or {}).items():
        if v.get("usado_pct") is None:
            continue
        renova = v.get("renova_em")
        quando = f", renova às {time.strftime('%d/%m %H:%M', time.localtime(renova))}" if renova else ""
        print(f"- {NOMES.get(nome, nome)}: {v['usado_pct']:.0f}% usado, {100 - v['usado_pct']:.0f}% livre{quando}")
    if r.get("contexto_tokens") is not None:
        print(f"- contexto: {r['contexto_tokens'] / 1000:.0f} mil tokens ({r.get('contexto_pct') or 0:.0f}% da janela)")
    if not r.get("limites"):
        print("- limites de uso: não informados (só aparecem para assinantes do Claude.ai ou atrás de gateway com limite)")
    sys.exit(1 if idade > VELHO else 0)


if __name__ == "__main__":
    main()

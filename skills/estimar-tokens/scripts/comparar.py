#!/usr/bin/env python3
"""Relatório estimado x realizado do pedido atual de uma sessão, com exportação em Markdown.

O pedido é aberto pelo hook do modo estimativa (modo.py) e a estimativa é gravada
por `estimar.py --registrar <sessão>`. O realizado é o custo real da sessão,
com subagentes, desde o início do pedido.

    comparar.py --sessao <id> [--md relatorio.md]
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402
import custo_real  # noqa: E402
import modo  # noqa: E402


def diferenca(estimado, real, fmt):
    if estimado is None or real is None:
        return "—"
    if not estimado:
        return fmt(real - estimado)
    return f"{fmt(real - estimado)} ({(real - estimado) / estimado:+.0%})"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sessao", help="ID da sessão (padrão: a atual)")
    ap.add_argument("--md", help="grava o relatório neste arquivo Markdown")
    a = ap.parse_args()

    sid = a.sessao or comum.sessao_atual()
    pedido = modo.ler_pedido(sid) if sid else None
    if not pedido:
        sys.exit("Nenhum pedido aberto nesta sessão. Ligue o modo com `/estimar-tokens on`.")
    principal, subagentes = comum.arquivos_da_sessao(sid)
    if not principal:
        sys.exit(f"Sessão {sid} não encontrada em {comum.PROJETOS}.")

    precos = comum.carregar_precos()
    real_tokens = real_chamadas = 0
    real_usd = 0.0
    for por_modelo in (custo_real.somar(principal, pedido["inicio"]), custo_real.somar(subagentes, pedido["inicio"])):
        for modelo, c in por_modelo.items():
            real_chamadas += c["chamadas"]
            real_tokens += sum(c[k] for k in custo_real.CAMPOS)
            valor = comum.custo_usd(precos, modelo, **{k: c[k] for k in custo_real.CAMPOS})
            real_usd = None if valor is None or real_usd is None else real_usd + valor

    est = pedido.get("estimativa")
    inicio = datetime.strptime(pedido["inicio"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).astimezone()
    linhas = [
        f"# Estimado x realizado: {est['titulo'] if est else pedido.get('pedido') or 'pedido'}",
        "",
        f"- Sessão: `{sid}`",
        f"- Pedido desde: {inicio.strftime('%d/%m/%Y %H:%M')}",
        "",
        "| | Estimado | Realizado | Diferença |",
        "| --- | ---: | ---: | ---: |",
    ]
    if est:
        linhas += [
            f"| Chamadas | {est['chamadas']} | {real_chamadas} | {diferenca(est['chamadas'], real_chamadas, lambda v: f'{v:+d}')} |",
            f"| Tokens processados | {comum.mil(est['tokens'])} | {comum.mil(real_tokens)} | "
            f"{diferenca(est['tokens'], real_tokens, lambda v: ('+' if v >= 0 else '') + comum.mil(v))} |",
            f"| Custo | {comum.usd(est.get('usd'))} | {comum.usd(real_usd)} | "
            f"{diferenca(est.get('usd'), real_usd, lambda v: ('+' if v >= 0 else '−') + comum.usd(abs(v)))} |",
        ]
    else:
        linhas += [
            f"| Chamadas | — | {real_chamadas} | — |",
            f"| Tokens processados | — | {comum.mil(real_tokens)} | — |",
            f"| Custo | — | {comum.usd(real_usd)} | — |",
            "",
            "Este pedido não teve estimativa registrada (`estimar.py --registrar`).",
        ]
    linhas += ["", "Inclui os subagentes da sessão. " + comum.AVISO_USD]
    texto = "\n".join(linhas) + "\n"
    print(texto)
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8")
        print(f"Gravado em {a.md}")
    pedido["relatado"] = True
    modo.gravar_pedido(sid, pedido)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Custo real (tokens e US$) de uma sessão do Claude Code, com exportação em Markdown.

Lê o registro da sessão em ~/.claude/projects e os dos subagentes dela, e soma
o usage de cada resposta por modelo.

    custo_real.py                         # sessão atual, inteira
    custo_real.py --ultimos-min 30        # só os últimos 30 minutos
    custo_real.py --desde "2026-11-10 09:00" --md custo.md
    custo_real.py --sessao <id>
"""

import argparse
import collections
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

CAMPOS = ("entrada", "escrita_5m", "escrita_1h", "leitura", "saida")


def iso_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def somar(arquivos, desde):
    por_modelo = collections.defaultdict(lambda: collections.Counter())
    for arq in arquivos:
        for r in comum.respostas_com_modelo(arq, desde):
            c = por_modelo[r["modelo"]]
            c.update(comum.uso_detalhado(r["uso"]))
            c["chamadas"] += 1
    return por_modelo


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sessao", help="ID da sessão (padrão: a atual)")
    ap.add_argument("--desde", help='início, hora local: "AAAA-MM-DD HH:MM"')
    ap.add_argument("--ultimos-min", type=int, help="só os últimos N minutos")
    ap.add_argument("--titulo", default="Custo real", help="título do relatório")
    ap.add_argument("--md", help="grava o relatório neste arquivo Markdown")
    a = ap.parse_args()

    sid = a.sessao or comum.sessao_atual()
    if not sid:
        sys.exit("Nenhuma sessão encontrada.")
    principal, subagentes = comum.arquivos_da_sessao(sid)
    if not principal:
        sys.exit(f"Sessão {sid} não encontrada em {comum.PROJETOS}.")

    desde = None
    if a.ultimos_min:
        desde = iso_utc(datetime.fromtimestamp(time.time() - a.ultimos_min * 60))
    elif a.desde:
        try:
            desde = iso_utc(datetime.strptime(a.desde, "%Y-%m-%d %H:%M").astimezone())
        except ValueError:
            sys.exit('Use --desde "AAAA-MM-DD HH:MM".')

    precos = comum.carregar_precos()
    grupos = [("Conversa principal", somar(principal, desde))]
    if subagentes:
        grupos.append((f"Subagentes ({len(subagentes)})", somar(subagentes, desde)))

    periodo = "sessão inteira"
    if desde:
        periodo = "desde " + datetime.strptime(desde, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")
    linhas = [
        f"# {a.titulo}",
        "",
        f"- Sessão: `{sid}`",
        f"- Período: {periodo}",
        f"- Gerado em: {time.strftime('%d/%m/%Y %H:%M')}",
        "",
        "| Origem | Modelo | Chamadas | Entrada | Escrita cache | Leitura cache | Saída | Custo |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    total = collections.Counter()
    total_usd = 0.0
    sem_preco = set()
    for nome, por_modelo in grupos:
        for modelo, c in sorted(por_modelo.items(), key=lambda kv: -kv[1]["chamadas"]):
            valor = comum.custo_usd(precos, modelo, **{k: c[k] for k in CAMPOS})
            if valor is None:
                sem_preco.add(modelo)
            else:
                total_usd += valor
            total.update(c)
            linhas.append(
                f"| {nome} | `{modelo}` | {c['chamadas']} | {comum.mil(c['entrada'])} | "
                f"{comum.mil(c['escrita_5m'] + c['escrita_1h'])} | {comum.mil(c['leitura'])} | "
                f"{comum.mil(c['saida'])} | {comum.usd(valor)} |"
            )
    if not total["chamadas"]:
        sys.exit("Nenhuma resposta no período.")
    linhas += [
        f"| **Total** | | **{total['chamadas']}** | **{comum.mil(total['entrada'])}** | "
        f"**{comum.mil(total['escrita_5m'] + total['escrita_1h'])}** | **{comum.mil(total['leitura'])}** | "
        f"**{comum.mil(total['saida'])}** | **{comum.usd(total_usd)}** |",
        "",
        f"Tokens novos (entrada + escrita no cache + saída): "
        f"{comum.mil(total['entrada'] + total['escrita_5m'] + total['escrita_1h'] + total['saida'])}. "
        f"Relidos do cache: {comum.mil(total['leitura'])}.",
        "",
        comum.AVISO_USD,
    ]
    if sem_preco:
        linhas += ["", "Sem preço na tabela (fora do total): " + ", ".join(f"`{m}`" for m in sorted(sem_preco)) + "."]
    texto = "\n".join(linhas) + "\n"
    print(texto)
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8")
        print(f"Gravado em {a.md}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Estima tokens e custo em US$ de uma lista de etapas, com exportação em Markdown.

Cada etapa é "descrição|chamadas|tokens novos em mil". Exemplo:

    estimar.py --etapa "Ler o código|4|8" --etapa "Corrigir e testar|8|15" --md estimativa.md

Modelo: a cada chamada o contexto inteiro é relido do cache, e os tokens novos
são gravados no cache ou gerados como saída. O contexto cresce com os tokens
novos de cada etapa. Sem --contexto, usa o contexto gravado pela status line.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

FRACAO_SAIDA = 0.3  # parte dos tokens novos que é saída do modelo; o resto vira escrita no cache


def ler_etapas(itens):
    etapas = []
    for item in itens:
        partes = [p.strip() for p in item.split("|")]
        if len(partes) != 3:
            sys.exit(f'Etapa inválida: "{item}". Use "descrição|chamadas|tokens novos em mil".')
        try:
            etapas.append((partes[0], int(partes[1]), float(partes[2].replace(",", ".")) * 1000))
        except ValueError:
            sys.exit(f'Etapa inválida: "{item}". Chamadas e tokens novos precisam ser números.')
    return etapas


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--etapa", action="append", default=[], help='"descrição|chamadas|novos em mil" (repita)')
    ap.add_argument("--arquivo", help="arquivo com uma etapa por linha, no mesmo formato")
    ap.add_argument("--contexto", type=float, help="contexto atual em mil tokens (padrão: o da status line)")
    ap.add_argument("--modelo", help="ID do modelo (padrão: o da sessão atual)")
    ap.add_argument("--titulo", default="Estimativa", help="título do relatório")
    ap.add_argument("--md", help="grava a estimativa neste arquivo Markdown")
    ap.add_argument("--registrar", metavar="SESSAO", help="grava o total como estimativa do pedido atual (modo estimativa)")
    a = ap.parse_args()

    itens = list(a.etapa)
    if a.arquivo:
        itens += [l for l in Path(a.arquivo).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    etapas = ler_etapas(itens)
    if not etapas:
        sys.exit("Nenhuma etapa. Use --etapa ou --arquivo.")

    precos = comum.carregar_precos()
    modelo = a.modelo or comum.modelo_recente()
    if comum.preco_modelo(precos, modelo) is None:
        print(f"Aviso: sem preço para {modelo}; os valores em US$ ficam em branco.", file=sys.stderr)
    contexto = a.contexto * 1000 if a.contexto is not None else (comum.contexto_atual() or 50_000)
    origem = "informado" if a.contexto is not None else ("da status line" if comum.contexto_atual() else "padrão, sem status line")

    linhas = [
        f"# {a.titulo}",
        "",
        f"- Data: {time.strftime('%d/%m/%Y %H:%M')}",
        f"- Modelo: `{modelo}`",
        f"- Contexto inicial: {comum.mil(contexto)} tokens ({origem})",
        "",
        "| # | Etapa | Chamadas | Tokens novos | Tokens processados | Custo |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    tot_ch = tot_novos = tot_proc = 0
    tot_usd = 0.0
    for i, (desc, chamadas, novos) in enumerate(etapas, 1):
        relidos = chamadas * contexto
        saida = novos * FRACAO_SAIDA
        escrita = novos - saida
        valor = comum.custo_usd(precos, modelo, escrita_1h=escrita, leitura=relidos, saida=saida)
        linhas.append(
            f"| {i} | {desc} | {chamadas} | {comum.mil(novos)} | {comum.mil(relidos + novos)} | {comum.usd(valor)} |"
        )
        tot_ch += chamadas
        tot_novos += novos
        tot_proc += relidos + novos
        tot_usd = None if valor is None or tot_usd is None else tot_usd + valor
        contexto += novos
    linhas += [
        f"| | **Total** | **{tot_ch}** | **{comum.mil(tot_novos)}** | **{comum.mil(tot_proc)}** | **{comum.usd(tot_usd)}** |",
        "",
        "Tokens processados = chamadas × contexto (relido do cache) + tokens novos. "
        f"Dos tokens novos, {FRACAO_SAIDA:.0%} contam como saída e o resto como escrita no cache (TTL 1 h).",
        "",
        comum.AVISO_USD,
    ]
    texto = "\n".join(linhas) + "\n"
    print(texto)
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8")
        print(f"Gravado em {a.md}")
    if a.registrar:
        import modo

        pedido = modo.ler_pedido(a.registrar) or {"inicio": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())}
        pedido["estimativa"] = {"titulo": a.titulo, "chamadas": tot_ch, "tokens": tot_proc, "usd": tot_usd}
        modo.gravar_pedido(a.registrar, pedido)
        print("Estimativa registrada para o relatório estimado x realizado (comparar.py).")


if __name__ == "__main__":
    main()

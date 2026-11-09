#!/usr/bin/env python3
"""Mede o custo real em tokens de cada ferramenta a partir do histórico do Claude Code.

Lê os registros de conversa em ~/.claude/projects/**/*.jsonl. O custo de uma
chamada de ferramenta é o quanto o contexto cresce da resposta que a chamou até
a resposta seguinte: inclui a própria chamada e o resultado que voltou. Para
subagentes, soma também o que o subagente processou na conversa dele.

Uso:
    calibrar.py [--dias N] [--projeto TRECHO] [--salvar]

--salvar grava a tabela em ~/.claude/estimar-tokens/custos-medidos.md, que a
skill estimar-tokens consulta antes da tabela padrão.
"""

import argparse
import collections
import json
import statistics
import sys
import time
from pathlib import Path

PROJETOS = Path.home() / ".claude" / "projects"
SAIDA = Path.home() / ".claude" / "estimar-tokens" / "custos-medidos.md"
MINIMO_AMOSTRAS = 3


def contexto(uso):
    return (
        uso.get("input_tokens", 0)
        + uso.get("cache_creation_input_tokens", 0)
        + uso.get("cache_read_input_tokens", 0)
    )


def respostas(arquivo):
    """Respostas do assistente na ordem, juntando os pedaços de uma mesma mensagem."""
    por_id = {}
    ordem = []
    lateral = False
    with open(arquivo, encoding="utf-8", errors="replace") as f:
        for linha in f:
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            if d.get("type") != "assistant":
                continue
            m = d.get("message") or {}
            uso = m.get("usage")
            mid = m.get("id")
            if not uso or not mid:
                continue
            lateral = lateral or bool(d.get("isSidechain"))
            if mid not in por_id:
                por_id[mid] = {"uso": uso, "ferramentas": []}
                ordem.append(mid)
            else:
                por_id[mid]["uso"] = uso
            for c in m.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    por_id[mid]["ferramentas"].append(c.get("name", "?"))
    return [por_id[i] for i in ordem], lateral


def percentil(valores, p):
    v = sorted(valores)
    return v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))]


def mil(n):
    return f"{n / 1000:.1f} mil"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dias", type=int, default=30, help="janela em dias (padrão: 30)")
    ap.add_argument("--projeto", default="", help="só projetos cujo diretório contém este trecho")
    ap.add_argument("--salvar", action="store_true", help=f"grava a tabela em {SAIDA}")
    a = ap.parse_args()

    limite = time.time() - a.dias * 86400
    arquivos = [
        p for p in PROJETOS.glob("**/*.jsonl")
        if p.stat().st_mtime >= limite and a.projeto in str(p.relative_to(PROJETOS))
    ]
    if not arquivos:
        sys.exit(f"Nenhum registro em {PROJETOS} nos últimos {a.dias} dias.")

    custos = collections.defaultdict(list)
    subagentes = []
    chamadas_api = []
    sessao_recente = None

    for arq in arquivos:
        rs, lateral = respostas(arq)
        if not rs:
            continue
        if lateral:
            subagentes.append(sum(contexto(r["uso"]) + r["uso"].get("output_tokens", 0) for r in rs))
            continue
        chamadas_api.extend(contexto(r["uso"]) for r in rs)
        for atual, prox in zip(rs, rs[1:]):
            if not atual["ferramentas"]:
                continue
            delta = contexto(prox["uso"]) - contexto(atual["uso"])
            if delta <= 0:  # compactação ou troca de contexto
                continue
            parte = delta / len(atual["ferramentas"])
            for nome in atual["ferramentas"]:
                custos[nome].append(parte)
        if sessao_recente is None or arq.stat().st_mtime > sessao_recente[0]:
            sessao_recente = (arq.stat().st_mtime, contexto(rs[-1]["uso"]))

    linhas = [
        f"# Custos medidos ({time.strftime('%d/%m/%Y')}, últimos {a.dias} dias, {len(arquivos)} registros)",
        "",
        "Tokens que cada chamada acrescenta ao contexto (chamada + resultado).",
        "",
        "| Ferramenta | Chamadas | Mediana | p90 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for nome, v in sorted(custos.items(), key=lambda kv: -statistics.median(kv[1])):
        if len(v) < MINIMO_AMOSTRAS:
            continue
        linhas.append(f"| {nome} | {len(v)} | {mil(statistics.median(v))} | {mil(percentil(v, 90))} |")
    if len(subagentes) >= MINIMO_AMOSTRAS:
        linhas += [
            "",
            f"Subagente, total processado na conversa dele ({len(subagentes)} subagentes): "
            f"mediana {mil(statistics.median(subagentes))}, p90 {mil(percentil(subagentes, 90))}.",
        ]
    if chamadas_api:
        linhas += [
            "",
            f"Contexto relido a cada resposta: mediana {mil(statistics.median(chamadas_api))}, "
            f"p90 {mil(percentil(chamadas_api, 90))}. Em conversa longa, cada chamada fica mais cara.",
        ]
    if sessao_recente:
        linhas += ["", f"Contexto da sessão mais recente agora: {mil(sessao_recente[1])}."]

    texto = "\n".join(linhas) + "\n"
    print(texto)
    if a.salvar:
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        SAIDA.write_text(texto, encoding="utf-8")
        print(f"Gravado em {SAIDA}")


if __name__ == "__main__":
    main()

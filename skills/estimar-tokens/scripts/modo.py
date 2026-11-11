#!/usr/bin/env python3
"""Modo estimativa: com ele ligado, todo pedido tem estimativa antes e relatório estimado x realizado no fim.

    modo.py on | off | status [--sessao ID]   # liga, desliga ou mostra o modo da sessão
    modo.py config [on|off]                   # sessões novas começam com o modo ligado ou não
    modo.py hook-inicio                       # hook SessionStart: aplica a configuração na sessão nova
    modo.py hook-pedido                       # hook UserPromptSubmit: troca o modo com /estimar-tokens on|off e abre o pedido
    modo.py hook-parar                        # hook Stop: cobra o relatório uma vez, se o pedido ainda não teve

O modo vale por sessão e fica em ~/.claude/estimar-tokens/modo/<sessão>.
A configuração das sessões novas fica em ~/.claude/estimar-tokens/config.json; sem ela,
começam desligadas, a não ser que exista o antigo ~/.claude/estimar-tokens/lembrete ou ligado.
Cada pedido fica em ~/.claude/estimar-tokens/pedidos/<sessão>.json.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

ANTIGOS = (comum.PASTA_USUARIO / "ligado", comum.PASTA_USUARIO / "lembrete")
CONFIG = comum.PASTA_USUARIO / "config.json"
MODOS = comum.PASTA_USUARIO / "modo"
PEDIDOS = comum.PASTA_USUARIO / "pedidos"
SCRIPTS = Path(__file__).resolve().parent
COMANDO = re.compile(r"\s*/estimar-tokens(?::estimar-tokens)?\s+(on|off)\s*$", re.IGNORECASE)


def nome_seguro(sid):
    return re.sub(r"[^A-Za-z0-9_-]", "_", sid)


def ligado(sid):
    try:
        return bool(sid) and (MODOS / nome_seguro(sid)).read_text().strip() == "on"
    except OSError:
        return False


def ligar(sid, on):
    MODOS.mkdir(parents=True, exist_ok=True)
    (MODOS / nome_seguro(sid)).write_text("on" if on else "off")


def inicia_ligado():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")).get("iniciar") == "on"
    except (OSError, ValueError, AttributeError):
        return any(p.exists() for p in ANTIGOS)


def configurar(on):
    comum.PASTA_USUARIO.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"iniciar": "on" if on else "off"}), encoding="utf-8")
    for p in ANTIGOS:
        p.unlink(missing_ok=True)


def estado(sid):
    if ligado(sid):
        return "Modo estimativa ligado nesta sessão: todo pedido tem estimativa antes e relatório estimado x realizado no fim. Desligue com `/estimar-tokens off`."
    return "Modo estimativa desligado nesta sessão. Ligue com `/estimar-tokens on`."


def aviso_ligado(sid):
    return (
        "[estimar-tokens] Modo estimativa ligado. Antes de agir, estime o pedido com "
        f'`python3 {SCRIPTS}/estimar.py --registrar {sid} --titulo "<pedido>" --etapa "..."` '
        "e avise o custo. Ao terminar, mostre o estimado x realizado com "
        f"`python3 {SCRIPTS}/comparar.py --sessao {sid}`."
    )


def arquivo_pedido(sid):
    return PEDIDOS / f"{nome_seguro(sid)}.json"


def ler_pedido(sid):
    try:
        return json.loads(arquivo_pedido(sid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def gravar_pedido(sid, pedido):
    PEDIDOS.mkdir(parents=True, exist_ok=True)
    destino = arquivo_pedido(sid)
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(pedido, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(destino)


def saldo_resumido():
    try:
        r = json.loads((comum.PASTA_USUARIO / "saldo.json").read_text())
        if time.time() - r.get("gravado_em", 0) >= 600:
            return ""
        partes = [
            f"{n} {v['usado_pct']:.0f}% usado"
            for n, v in (r.get("limites") or {}).items()
            if v.get("usado_pct") is not None
        ]
        if r.get("contexto_tokens"):
            partes.append(f"contexto {r['contexto_tokens'] / 1000:.0f} mil")
        return " Saldo: " + ", ".join(partes) + "." if partes else ""
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return ""


def entrada_hook():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def aplicar_config(sid):
    """Sessão sem modo gravado começa conforme a configuração (modo.py config)."""
    if not (MODOS / nome_seguro(sid)).exists():
        ligar(sid, inicia_ligado())


def hook_inicio():
    sid = entrada_hook().get("session_id")
    if not sid:
        return
    aplicar_config(sid)
    if ligado(sid):
        print(f"[estimar-tokens] {estado(sid)}")


def hook_pedido():
    d = entrada_hook()
    sid = d.get("session_id")
    if not sid:
        return
    m = COMANDO.match(d.get("prompt") or "")
    if m:
        ligar(sid, m.group(1).lower() == "on")
        print(f"[estimar-tokens] {estado(sid)} Sessão: {sid}.")
        return
    aplicar_config(sid)
    if not ligado(sid):
        return
    gravar_pedido(sid, {
        "inicio": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "pedido": (d.get("prompt") or "").strip()[:200],
    })
    print(aviso_ligado(sid) + saldo_resumido())


def hook_parar():
    d = entrada_hook()
    sid = d.get("session_id")
    if not ligado(sid) or d.get("stop_hook_active"):
        return
    pedido = ler_pedido(sid)
    if not pedido or pedido.get("relatado") or pedido.get("cobrado"):
        return
    pedido["cobrado"] = True
    gravar_pedido(sid, pedido)
    print(json.dumps({
        "decision": "block",
        "reason": "[estimar-tokens] Modo estimativa ligado: antes de encerrar, rode "
        f"`python3 {SCRIPTS}/comparar.py --sessao {sid}` e mostre ao usuário o estimado x realizado deste pedido.",
    }, ensure_ascii=False))


def main():
    args = sys.argv[1:] or ["status"]
    acao = args[0]
    if acao in ("on", "off", "status"):
        sid = args[args.index("--sessao") + 1] if "--sessao" in args[:-1] else comum.sessao_atual()
        if not sid:
            sys.exit("Sessão não identificada. Use --sessao <id>.")
        if acao != "status":
            ligar(sid, acao == "on")
        print(estado(sid))
    elif acao == "config":
        if len(args) > 1:
            if args[1] not in ("on", "off"):
                sys.exit("Use: modo.py config [on|off]")
            configurar(args[1] == "on")
        print(f"Novas sessões começam com o modo estimativa {'ligado' if inicia_ligado() else 'desligado'}.")
    elif acao == "hook-inicio":
        hook_inicio()
    elif acao == "hook-pedido":
        hook_pedido()
    elif acao == "hook-parar":
        hook_parar()
    else:
        sys.exit("Use: modo.py on | off | status [--sessao ID] | config [on|off]")


if __name__ == "__main__":
    main()

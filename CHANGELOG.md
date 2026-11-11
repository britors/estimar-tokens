# Changelog

## 1.4.0 — 11/11/2026

- Modo estimativa por sessão, ligado com `/estimar-tokens on` e desligado com `/estimar-tokens off` (`scripts/modo.py`). Ligado, todo pedido tem estimativa antes e relatório estimado x realizado no fim; o hook Stop cobra o relatório uma vez se ele faltar.
- `/estimar-tokens:setup`: pergunta se as sessões novas começam com o modo estimativa ligado (`modo.py config on|off`, hook SessionStart).
- `scripts/estimar.py --registrar <sessão>`: grava a estimativa do pedido.
- `scripts/comparar.py`: tabela estimado x realizado (chamadas, tokens, US$) desde o início do pedido, com subagentes, exportável em Markdown.
- O hook de lembrete (`hooks/lembrete.py`) foi substituído pelo modo estimativa; quem tinha o arquivo antigo `~/.claude/estimar-tokens/lembrete` começa as sessões novas com o modo ligado, até rodar o setup.

## 1.3.0 — 10/11/2026

- Status line: os percentuais de 5 h, 7 dias e contexto aparecem como barras (`5h ███▍░░░░ 42%`).
- Status line: segunda linha com os tokens e o custo em US$ da sessão, com os subagentes. A leitura do registro é incremental, com cache em `~/.claude/estimar-tokens/sessoes/`.

## 1.2.0 — 10/11/2026

- Custo em US$: `references/precos.json` traz os preços por modelo, com os multiplicadores de cache; dá para sobrescrever em `~/.claude/estimar-tokens/precos.json`.
- `scripts/estimar.py`: estimativa por etapa em tokens e US$, exportável em Markdown (`--md`).
- `scripts/custo_real.py`: custo real de uma sessão, com subagentes, por modelo e período, exportável em Markdown (`--md`).
- SKILL.md: aviso de custo em US$, custo de cache frio depois de pausas e seção de exportação.

## 1.1.0 — 09/11/2026

- Saldo real: `scripts/statusline.py` mostra e grava o uso dos limites de 5 h e 7 dias e do contexto; `scripts/saldo.py` lê o último retrato.
- `scripts/calibrar.py` mede o custo real de cada ferramenta no histórico local (`--dias`, `--projeto`, `--salvar`).
- SKILL.md:
  - novo modelo de estimativa: chamadas × contexto + acréscimos;
  - decisões tomadas a partir do saldo;
  - descrição bilíngue, em terceira pessoa.
- `references/custos.md`: tabela padrão com valores medidos.
- Hook opcional `UserPromptSubmit`, desligado por padrão.
- README em português e inglês; CI que valida o plugin.

## 1.0.0 — 09/11/2026

- Primeira versão: a skill, o ícone e o marketplace.

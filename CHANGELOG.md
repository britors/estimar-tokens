# Changelog

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

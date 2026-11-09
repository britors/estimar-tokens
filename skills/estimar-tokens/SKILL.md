---
name: estimar-tokens
description: Esta skill deve ser usada antes de tarefas com vários passos, subagentes, builds, CI, revisões ou leitura de muitos arquivos, e quando o usuário pedir para "estimar tokens", "quanto vai gastar", "temos saldo?", "quanto falta do limite" ou "não pare no meio por limite". This skill should be used before multi-step tasks, subagents, builds, CI or large reads, and when the user asks to "estimate tokens", "how much will this cost", "how much quota is left" or "don't hit the usage limit".
---

# Estimar tokens antes de agir

Objetivo: a sessão não pode parar no meio de uma tarefa por limite de uso. Antes de cada etapa, estime o custo, compare com o saldo e só comece o que cabe.

Os scripts citados ficam na pasta `scripts/`, ao lado deste SKILL.md. Use o caminho absoluto deles.

## 1. Ler o saldo

Rode `python3 <pasta desta skill>/scripts/saldo.py`.

- **Código 0:** há um retrato recente do uso, com os limites de 5 horas e de 7 dias, o horário de renovação e o tamanho do contexto. Use esses números.
- **Código 1:** o retrato tem mais de 10 minutos. Use-o com cautela.
- **Código 2:** a status line do plugin não está configurada. Diga ao usuário uma vez que o saldo real só aparece com ela (veja o README) e siga só com estimativas.

O saldo vem em percentual do limite, não em tokens. Para converter, anote o percentual antes e depois de uma etapa cujo custo você estimou. A razão dá quantos tokens vale 1% nesta sessão.

## 2. Escolher a tabela de custos

1. Se `~/.claude/estimar-tokens/custos-medidos.md` existir, use-o: são os custos reais deste usuário, medidos por `scripts/calibrar.py --salvar`.
2. Senão, use `references/custos.md`.
3. Se a tabela medida tiver mais de 30 dias, sugira recalibrar.

## 3. Estimar cada etapa

Quebre a tarefa em etapas que terminem num **estado consistente**: commit feito, PR aberto, pacote enviado, relatório salvo. Nunca deixe estado público pela metade, como uma tag sem pacote ou um build sem registro.

Para cada etapa:

```
custo ≈ chamadas × contexto atual  +  soma do que cada chamada acrescenta
```

- **Contexto atual:** vem do `saldo.py`, ou estime pelo tamanho da conversa. Ele é relido a cada resposta, a maior parte do cache, e domina o custo em conversa longa.
- **O que cada chamada acrescenta:** vem da tabela de custos.
- **Subagente:** conte o total da conversa dele, que é bem maior que o relatório que ele devolve.

## 4. Avisar e decidir

Antes de executar, diga numa linha: `Próxima etapa: <o quê>. Estimativa: ~N mil tokens.`

| Situação | O que fazer |
| --- | --- |
| Etapa até 20 mil e limite de 5h abaixo de 80% | Avise e siga. |
| Etapa de 20 a 60 mil | Avise e siga, a não ser que o usuário tenha pedido para confirmar. |
| Etapa acima de 60 mil, ou subagentes em paralelo | **Pergunte antes** e proponha uma versão mais barata. |
| Limite de 5h em 80% ou mais | Só etapas pequenas. Avise o horário de renovação. |
| Limite de 5h em 90% ou mais, ou a etapa não cabe no que resta | Não comece. Termine num estado consistente, resuma o que falta e proponha continuar depois da renovação. |
| Limite de 7 dias em 90% ou mais | Avise que o limite semanal está no fim, antes de qualquer etapa grande. |

Durante a execução, se a etapa passar de 1,5× o estimado, pare num ponto consistente e avise.

## 5. Gastar menos

- Filtre a saída: `--jq`, `grep`, `head`, `tail`, `wc -l`. Nunca jogue um log ou diff inteiro no contexto.
- Leia só o trecho necessário, com offset e limit.
- Junte comandos independentes numa chamada só. Cada chamada relê o contexto inteiro.
- Use subagentes só quando o usuário pedir, poucos de cada vez, e mande gravarem o resultado em arquivo.
- Espere CI ou build com um loop silencioso que imprime só o resultado final.
- Não repita pesquisa já feita na conversa ou na memória.
- Em conversa muito longa, prefira terminar a etapa e sugerir compactar ou recomeçar.

## Recursos

- `scripts/saldo.py`: último saldo gravado pela status line.
- `scripts/statusline.py`: status line que mostra e grava o saldo; aceita `--encadear` para manter outra status line.
- `scripts/calibrar.py`: mede custos reais no histórico (`--dias`, `--projeto`, `--salvar`).
- `references/custos.md`: tabela padrão, para quando não houver medição.

---
name: estimar-tokens
description: Estima quantos tokens uma tarefa vai gastar antes de começar e divide o trabalho em etapas que terminam num estado consistente, para a sessão não parar no meio por limite de uso. Use antes de qualquer operação com vários passos, subagentes, builds, CI, revisões ou leitura de muitos arquivos, ou quando o usuário pedir "estime", "quanto vai gastar" ou "temos saldo?".
---

# Estimar tokens antes de agir

Não dá para ver o saldo restante da cota do usuário. Esta skill não mede saldo: ela **estima o custo** de cada etapa, avisa antes de começar e evita deixar trabalho pela metade.

## Passos

1. **Quebre a tarefa em etapas.** Cada etapa precisa terminar num estado consistente: commit feito, PR aberto, pacote enviado ou relatório salvo. Nada de estado público pela metade, como uma tag sem pacote ou um build sem registro.
2. **Estime cada etapa** com a tabela abaixo. Some e arredonde para cima.
3. **Avise antes de executar**, numa linha: `Próxima etapa: <o quê>. Estimativa: ~N mil tokens.`
4. **Confirme quando o custo for alto:**
   - até 20 mil: avise e siga;
   - de 20 a 60 mil: avise e siga, a não ser que o usuário tenha pedido para confirmar;
   - acima de 60 mil, ou com subagentes em paralelo: **pergunte antes** e proponha uma versão mais barata.
5. **Durante a execução:** se a etapa passar de 1,5× o estimado, pare num ponto consistente e avise.

## Tabela de custo aproximado

| Operação | Tokens (aprox.) |
| --- | --- |
| Comando curto (status, ls, gh view com `--jq`) | 0,5–1 mil |
| Ler um arquivo médio inteiro (300 linhas) | 4–6 mil |
| Ler trecho com offset/limit ou grep | 1–2 mil |
| Editar arquivo (Edit) | 1–2 mil |
| Criar arquivo novo (Write) | tamanho do arquivo + 1 mil |
| Log de CI filtrado (grep/tail) | 1–3 mil |
| Log de CI ou diff inteiro, sem filtro | 10–50 mil, **evite** |
| Esperar CI/build em loop silencioso | 1–2 mil |
| Commit + push + abrir PR | 2–3 mil |
| Corrigir um bug pequeno (ler, editar, testar, PR) | 15–30 mil |
| Corrigir um bug médio, vários arquivos | 30–60 mil |
| Subagente (Explore, general-purpose) | 20–80 mil cada |
| Revisão com vários revisores em paralelo | 100–300 mil |
| Envio a um pacote OBS (_service, changes, commit) | 5–15 mil |
| Pergunta ao usuário (AskUserQuestion) | 1–2 mil |

Contexto acumulado também conta: em conversa longa, cada chamada fica mais cara. Se a conversa já está grande, prefira terminar a etapa e resumir.

## Como gastar menos

- Filtre a saída: `--jq`, `grep`, `head`, `tail`, `| wc -l`. Nunca jogue um log inteiro no contexto.
- Leia só o trecho necessário (offset/limit), não o arquivo todo.
- Junte comandos independentes numa chamada só.
- Use subagentes só quando o usuário pedir, um ou poucos de cada vez, e mande gravarem o resultado em arquivo aos poucos.
- Espere CI ou build com um loop silencioso que imprime só o resultado final, ou em segundo plano, sem consultar a saída repetidamente.
- Não repita pesquisa já feita na conversa ou na memória.

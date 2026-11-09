# Tabela padrão de custos

Use esta tabela quando não houver medição própria em `~/.claude/estimar-tokens/custos-medidos.md`. Para medir os seus custos, rode `scripts/calibrar.py --salvar`.

Os valores foram medidos em cerca de 1.300 chamadas reais (novembro de 2026) e arredondados para cima.

## O que cada chamada acrescenta ao contexto

| Operação | Mediana | Caso ruim (p90) |
| --- | ---: | ---: |
| Comando curto (Bash com saída filtrada, gh com `--jq`) | 1 mil | 2,5 mil |
| Ler trecho de arquivo (offset/limit) ou grep | 1 mil | 3 mil |
| Ler arquivo inteiro | 1 a 6 mil | 15 mil |
| Editar arquivo (Edit) | 0,6 mil | 1 mil |
| Criar arquivo (Write) | 1,7 mil + tamanho | 5 mil |
| Pergunta ao usuário | 1 mil | 1,5 mil |
| Busca na web | 1,7 mil | 2,6 mil |
| Log de CI ou diff **sem filtro** | 10 a 50 mil | — |
| Relatório devolvido por subagente | 1,2 mil | 3 mil |

## Custos que não aparecem na tabela acima

| Item | Valor típico |
| --- | --- |
| Contexto relido a cada resposta | é o tamanho da conversa; de 50 mil (início) a 800 mil (sessão longa) |
| Conversa inteira de um subagente | mediana 80 mil; os maiores passam de 1 milhão |
| Revisão com vários revisores em paralelo | 300 mil a vários milhões |

## Etapas típicas (chamadas × contexto + acréscimos)

Exemplo com contexto de 150 mil:

| Etapa | Chamadas | Custo aproximado |
| --- | ---: | ---: |
| Consultar um status | 1–2 | 150–300 mil processados, ~2 mil novos |
| Commit + push + PR | 2–3 | 300–450 mil processados, ~3 mil novos |
| Corrigir um bug pequeno | 8–15 | 1,2–2,2 milhões processados, ~20 mil novos |

A maior parte do que é processado vem do cache, que custa bem menos que tokens novos. Mesmo assim, o número de chamadas pesa: em conversa longa, juntar comandos economiza mais que encurtar a saída.

# estimar-tokens

Skill do [Claude Code](https://claude.com/claude-code) que estima quantos tokens cada etapa de uma tarefa vai gastar, **antes** de executá-la. Ela também divide o trabalho em etapas que terminam num estado consistente, para a sessão não parar no meio por limite de uso.

A skill não enxerga o saldo da sua cota, porque nenhuma ferramenta enxerga. O que ela faz:

- quebra a tarefa em etapas seguras;
- estima o custo de cada uma com uma tabela de referência;
- avisa antes de começar e pede confirmação quando o custo é alto;
- reduz o gasto com saídas filtradas, leitura parcial e poucos subagentes.

## Instalação

Para todos os seus projetos:

```bash
git clone https://github.com/britors/estimar-tokens.git ~/.claude/skills/estimar-tokens
```

Só para um projeto: clone em `.claude/skills/estimar-tokens` dentro do projeto.

## Uso

O Claude carrega a skill sozinho antes de tarefas com vários passos. Você também pode chamá-la com `/estimar-tokens`. Para que ela valha sempre, acrescente ao `CLAUDE.md`:

```markdown
Antes de cada operação, siga a skill `estimar-tokens`.
```

## Licença

GPL-3.0. Veja [LICENSE](LICENSE).

<p align="center">
  <img src=".claude-plugin/icon.svg" alt="Ícone do estimar-tokens: um medidor com a agulha antes da zona vermelha" width="128">
</p>

# estimar-tokens

Plugin do [Claude Code](https://claude.com/claude-code) que estima quantos tokens cada etapa de uma tarefa vai gastar, **antes** de executá-la. Ele também divide o trabalho em etapas que terminam num estado consistente, para a sessão não parar no meio por limite de uso.

## O que ele faz

O plugin não enxerga o saldo da sua cota, porque nenhuma ferramenta enxerga. O que ele faz:

- **Quebra a tarefa em etapas seguras.** Cada etapa termina com algo concluído (commit, PR, pacote enviado), sem deixar estado público pela metade.
- **Estima cada etapa** com uma tabela de referência (comando curto, leitura de arquivo, log de CI, correção de bug, subagente…).
- **Avisa antes de começar**, numa linha: `Próxima etapa: <o quê>. Estimativa: ~N mil tokens.`
- **Pede confirmação quando o custo é alto**, acima de 60 mil tokens ou com subagentes em paralelo, e propõe uma versão mais barata.
- **Gasta menos**: saídas filtradas, leitura parcial de arquivos, poucos subagentes e espera de CI sem consultas repetidas.

## Instalação

### Pelo Claude Code CLI (recomendado)

No Claude Code 2.1.275 ou mais novo, dentro de uma sessão:

```
/plugin install estimar-tokens --marketplace britors/estimar-tokens
```

Em versões anteriores, em dois passos:

```
/plugin marketplace add britors/estimar-tokens
/plugin install estimar-tokens@estimar-tokens
```

Pela linha de comando, fora da sessão:

```bash
claude plugin marketplace add britors/estimar-tokens
claude plugin install estimar-tokens@estimar-tokens
```

Para atualizar:

```
/plugin marketplace update estimar-tokens
```

### Manual, só a skill

Se preferir não usar o sistema de plugins, copie a skill para a sua pasta de skills:

```bash
git clone https://github.com/britors/estimar-tokens.git /tmp/estimar-tokens
mkdir -p ~/.claude/skills
cp -r /tmp/estimar-tokens/skills/estimar-tokens ~/.claude/skills/
```

Para um projeto só, use `.claude/skills/` dentro do projeto no lugar de `~/.claude/skills/`.

## Uso

O Claude carrega a skill sozinho antes de tarefas com vários passos. Você também pode chamá-la direto:

- instalada como plugin: `/estimar-tokens:estimar-tokens`;
- instalada manualmente: `/estimar-tokens`.

Para que ela valha sempre, acrescente ao `CLAUDE.md` do projeto, ou ao `~/.claude/CLAUDE.md`:

```markdown
Antes de cada operação, siga a skill `estimar-tokens`.
```

## Estrutura

```
.claude-plugin/
  marketplace.json   # catálogo com um plugin (este repo)
  plugin.json        # manifesto do plugin
  icon.svg, icon.png # ícone
skills/
  estimar-tokens/
    SKILL.md         # a skill: passos, tabela de custos e como gastar menos
```

Para ajustar a tabela de custos ao seu uso, edite `skills/estimar-tokens/SKILL.md`.

## Licença

GPL-3.0. Veja [LICENSE](LICENSE).

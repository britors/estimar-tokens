<p align="center">
  <img src=".claude-plugin/icon.svg" alt="Ícone do estimar-tokens: um medidor com a agulha antes da zona vermelha" width="128">
</p>

# estimar-tokens

[Português](#português) · [English](#english)

## Português

Plugin do [Claude Code](https://claude.com/claude-code) que estima quantos tokens cada etapa de uma tarefa vai gastar e compara com o **saldo real** dos seus limites de uso, **antes** de executar. Assim a sessão não para no meio de uma tarefa por limite.

### O que ele faz

- **Lê o saldo real.** Mostra o percentual usado dos limites de 5 horas e de 7 dias e o tamanho do contexto, a partir dos dados que o Claude Code envia à status line.
- **Estima cada etapa** pelo modelo `chamadas × contexto atual + acréscimos`, com custos **medidos no seu próprio histórico**.
- **Quebra a tarefa em etapas seguras**, que terminam com algo concluído (commit, PR, pacote enviado), sem estado público pela metade.
- **Decide pelo saldo:**
  - avisa o custo antes de cada etapa;
  - pede confirmação nas etapas caras;
  - não começa o que não cabe e propõe continuar depois da renovação do limite.
- **Gasta menos**: saídas filtradas, leitura parcial, poucos subagentes e menos chamadas.

### Instalação

No Claude Code 2.1.275 ou mais novo, dentro de uma sessão:

```
/plugin install estimar-tokens --marketplace britors/estimar-tokens
```

Em versões anteriores:

```
/plugin marketplace add britors/estimar-tokens
/plugin install estimar-tokens@estimar-tokens
```

Pela linha de comando:

```bash
claude plugin marketplace add britors/estimar-tokens
claude plugin install estimar-tokens@estimar-tokens
```

Para atualizar: `/plugin marketplace update estimar-tokens`.

**Manual, só a skill**, sem o sistema de plugins e sem o hook:

```bash
git clone https://github.com/britors/estimar-tokens.git ~/src/estimar-tokens
mkdir -p ~/.claude/skills
ln -s ~/src/estimar-tokens/skills/estimar-tokens ~/.claude/skills/estimar-tokens
```

### Configurar o saldo real (recomendado)

Sem este passo, a skill só estima. Com ele, ela sabe quanto do limite já foi usado.

Em `~/.claude/settings.json`, aponte a status line para o script do plugin. Instalado como plugin, ele fica em `~/.claude/plugins/marketplaces/estimar-tokens/skills/estimar-tokens/scripts/statusline.py`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/plugins/marketplaces/estimar-tokens/skills/estimar-tokens/scripts/statusline.py"
  }
}
```

Para manter a status line que você já usa, passe o comando dela em `--encadear`:

```json
"command": "python3 .../statusline.py --encadear 'bash ~/.claude/minha-statusline.sh'"
```

A barra mostra algo como `minha linha | 5h 42% · 7d 71% · ctx 13%`, e o retrato vai para `~/.claude/estimar-tokens/saldo.json`.

Os limites só aparecem para assinantes do Claude.ai, ou atrás de um gateway com limite de gasto. Pela API sem gateway, a status line mostra só o contexto.

### Calibrar com o seu histórico

```bash
python3 .../scripts/calibrar.py --salvar
```

O script lê `~/.claude/projects/**/*.jsonl` e mede quanto cada ferramenta acrescenta ao contexto (mediana e p90), quanto custa um subagente e o contexto típico das suas sessões. Ele grava o resultado em `~/.claude/estimar-tokens/custos-medidos.md`, e a skill passa a usar essa tabela no lugar da padrão.

Opções:

- `--dias N`: janela, padrão de 30 dias;
- `--projeto TRECHO`: só um projeto.

Nada sai da sua máquina.

### Lembrete a cada pedido (opcional)

O plugin traz um hook que lembra o Claude de estimar a cada pedido, com o saldo atual. Ele vem **desligado**: sem o arquivo de ativação, o hook não imprime nada nem gasta tokens.

```bash
mkdir -p ~/.claude/estimar-tokens
touch ~/.claude/estimar-tokens/lembrete   # liga (cerca de 60 tokens por pedido)
rm ~/.claude/estimar-tokens/lembrete      # desliga
```

### Uso

O Claude carrega a skill sozinho antes de tarefas com vários passos. Para chamar direto:

- instalada como plugin: `/estimar-tokens:estimar-tokens`;
- instalada manualmente: `/estimar-tokens`.

Para que ela valha sempre sem o hook, acrescente ao `CLAUDE.md`:

```markdown
Antes de cada operação, siga a skill `estimar-tokens`.
```

### Estrutura

```
.claude-plugin/          marketplace.json, plugin.json, ícone
hooks/                   lembrete opcional (UserPromptSubmit)
skills/estimar-tokens/
  SKILL.md               passos: saldo → tabela → estimativa → decisão
  references/custos.md   tabela padrão
  scripts/
    statusline.py        mostra e grava o saldo
    saldo.py             lê o último saldo
    calibrar.py          mede custos no histórico
```

Requer Python 3.8 ou mais novo, só com a biblioteca padrão.

## English

[Claude Code](https://claude.com/claude-code) plugin that estimates how many tokens each step of a task will use and checks it against your **real usage limits**, **before** running it, so a session doesn't stop halfway because of a usage limit.

- **Real balance:** the bundled status line script (`scripts/statusline.py`) shows and records the 5-hour and 7-day limit usage and context size that Claude Code sends to the status line. Use `--encadear '<cmd>'` to keep your current status line.
- **Measured costs:** `scripts/calibrar.py --salvar` measures per-tool cost from your own `~/.claude/projects` transcripts. Everything stays local.
- **Safe steps:** work is split into steps that end in a consistent state. Expensive steps need confirmation, and steps that don't fit the remaining quota aren't started.
- **Optional reminder hook:** off by default. Turn it on with `touch ~/.claude/estimar-tokens/lembrete`.

Install:

```
/plugin install estimar-tokens --marketplace britors/estimar-tokens
```

On older versions, run `/plugin marketplace add britors/estimar-tokens` and then `/plugin install estimar-tokens@estimar-tokens`.

The skill text is in Brazilian Portuguese, and Claude follows it in any language.

## Licença / License

GPL-3.0. Veja / see [LICENSE](LICENSE).

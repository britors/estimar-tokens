---
name: setup
description: Configura se as novas sessões começam com o modo estimativa ligado ou desligado. Use quando o usuário digitar /estimar-tokens:setup. Configures whether new sessions start with estimate mode on or off.
disable-model-invocation: true
---

# Configurar o estimar-tokens

O script fica em `../estimar-tokens/scripts/modo.py`, a partir da pasta deste SKILL.md. Use o caminho absoluto.

1. Rode `python3 <script> config` e mostre ao usuário a configuração atual.
2. Se o usuário já passou `on` ou `off` ao chamar `/estimar-tokens:setup`, use essa resposta. Senão, pergunte (com a ferramenta de perguntas, se houver) se o plugin deve iniciar automaticamente nas sessões novas:
   - **Sim:** toda sessão nova começa com o modo estimativa ligado. Todo pedido tem estimativa antes e relatório estimado x realizado no fim. O usuário desliga numa sessão com `/estimar-tokens off`.
   - **Não:** as sessões começam com o modo desligado. O usuário liga quando quiser, com `/estimar-tokens on`.
3. Grave a resposta com `python3 <script> config on` ou `python3 <script> config off` e confirme o que ficou.

A configuração vale para as sessões que começarem depois. Para a sessão atual, o usuário usa `/estimar-tokens on` ou `/estimar-tokens off`.

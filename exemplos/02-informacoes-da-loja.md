# 02 — Informações da loja

Endereço e horário vêm do manual de políticas (PDF). A cada mensagem, as três seções do manual mais próximas em significado são anexadas ao prompt (busca semântica com `bge-m3`), e o agente responde só com base nelas. Nenhuma tool é chamada.

Conversa nova, com contexto zerado:

```
Você: Qual o endereço da loja?

Assistente: O endereço da loja é Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333. Estamos há mais de 13 anos oferecendo instrumentos musicais para todos os gostos! 🎸

[trace] 15.2s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found

Você: vocês abrem no sábado?

Assistente: Sim, estamos abertos no sábado, das 09h às 13h. É um dia legal para visitar a loja e testar os instrumentos! 🎸 Se precisar de mais informações, é só perguntar.

[trace] 17.6s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- Endereço, CEP e o horário de sábado (09h às 13h) conferem com o manual.
- **Erro do modelo:** "há mais de 13 anos" está errado. O manual diz "mais de 15 anos" e a loja foi fundada em 2008. É um erro de cálculo do 8B; a conferência de fundamentação só confere preços e nomes em negrito, então não o pega.
- O agente informa os dias e o horário, mas não diz se a loja está aberta neste momento: ele não tem relógio.

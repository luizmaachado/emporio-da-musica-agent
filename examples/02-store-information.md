# 02 — Store information

Address and opening hours come from the store manual (PDF). On every message, the three manual sections closest in meaning are added to the prompt (semantic search with `bge-m3`), and the agent answers only from them. No tool is called.

A new conversation, with an empty history. The agent answers in Portuguese, the language of its customers:

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

## Notes
- The address, the postal code and the Saturday hours (9:00 to 13:00) match the manual.
- **Model error:** "há mais de 13 anos" ("for over 13 years") is wrong. The manual says "over 15 years" and the store was founded in 2008. It is an arithmetic mistake of the 8B model; the grounding check only verifies prices and bold names, so it does not catch it.
- The agent gives the opening days and hours but does not say whether the store is open right now: it has no clock.

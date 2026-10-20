# 04 — Payment

The payment rules (5% PIX discount that does not apply to promotional prices, installments by tier, nothing split under R$ 50.00) live in code. The `quote_payment` tool returns the finished quote and the model only repeats the values, without doing any arithmetic. In the second turn the answer comes from the conversation context, with no new call.

A new conversation, with an empty history. The agent answers in Portuguese, the language of its customers:

```
Você: Posso parcelar o Takamine GD20 em 10x?

Assistente: O Takamine GD20 pode ser parcelado em 10x de **R$ 219,90** (total de R$ 2.199,00). A partir de 7x, a parcela mínima é R$ 100,00, e essa opção atende à regra. 

Se quiser pagar à vista, o PIX dá **5% de desconto** (total de R$ 2.089,05). Também aceitamos cartão de débito ou boleto. Quer saber mais sobre outras formas de pagamento? 🎸

[trace] 82.6s, 2 tool call(s)
[trace]   search_products(query='Takamine GD20') -> 1 products
[trace]   quote_payment(product_id=95, installments=10) -> {"product": "Takamine GD20 Dreadnought Natural", "availability": "available", "l
[trace]   grounding: no ungrounded prices or names found

Você: e se eu pagar no pix?

Assistente: Se pagar no PIX, você ganha **5% de desconto** e paga **R$ 2.089,05** à vista (antes era R$ 2.199,00). É a forma mais rápida e econômica! 

Quer saber se pode combinar PIX com outra forma de pagamento? 🎸

[trace] 35.2s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found
```

## Notes
- Check: 10 installments of R$ 219.90 (2,199.00 ÷ 10) respect the R$ 100.00 minimum for 7x to 12x. PIX = 5% of R$ 2,199.00 = R$ 109.95, total R$ 2,089.05.
- This is the case that motivated the tool: before it, the agent did not look up the Takamine price to answer the installment question and asked the customer for the amount.
- The agent chained two tools (`search_products` to find the id and `quote_payment` with `installments=10`).

# 04 — Pagamento

As regras de pagamento (PIX com 5% de desconto que não vale em preço promocional, parcelas por faixa, nada é parcelado abaixo de R$ 50,00) estão no código. A tool `quote_payment` devolve a cotação pronta e o modelo apenas repete os valores, sem fazer conta. No segundo turno a resposta sai do contexto da conversa, sem nova chamada.

Conversa nova, com contexto zerado:

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

## Observações
- Conferência: 10x de R$ 219,90 (2.199,00 ÷ 10) respeita o mínimo de R$ 100,00 para 7x a 12x. PIX = 5% de R$ 2.199,00 = R$ 109,95, total R$ 2.089,05.
- Este é o caso que motivou a tool: antes dela, o agente não consultava o preço do Takamine para responder o parcelamento e pedia o valor ao cliente.
- O agente encadeou duas tools (`search_products` para achar o id e `quote_payment` com `installments=10`).

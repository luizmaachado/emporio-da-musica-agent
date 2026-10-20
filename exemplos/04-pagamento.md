# 04 — Pagamento

As regras de pagamento (PIX com 5% de desconto que não vale em preço promocional, parcelas por faixa, nada é parcelado abaixo de R$ 50,00) estão no código, e a tool `quote_payment` devolve a cotação pronta. O modelo apenas repete os valores, sem fazer conta.

## Todas as formas de pagamento

```
Você: quais opcoes de pagamento para o violao Takamine GD20

Assistente: Para o **Takamine GD20 Dreadnought Natural**, as opções de pagamento são:  

### **PIX**  
- **Total**: R$ 2.089,05 (com desconto de R$ 109,95).  

### **Cartão de Débito**  
- **Total**: R$ 2.199,00 (à vista).  

### **Boleto Bancário**  
- **Total**: R$ 2.199,00 (à vista).  

### **Cartão de Crédito**  
- **Até 12x sem juros** (mínimo R$ 100,00 por parcela):  
  - 1x: R$ 2.199,00  
  - 2x: R$ 1.099,50  
  - 3x: R$ 733,00  
  - 4x: R$ 549,75  
  - 5x: R$ 439,80  
  - 6x: R$ 366,50  
  - 7x: R$ 314,14  
  - 8x: R$ 274,88  
  - 9x: R$ 244,33  
  - 10x: R$ 219,90  
  - 11x: R$ 199,91  
  - 12x: R$ 183,25  

Precisa de ajuda para escolher a melhor opção? 😊

[trace] 146.5s, 1 tool call(s)
[trace]   quote_payment(product_id=95) -> {"product": "Takamine GD20 Dreadnought Natural", "availability": "available", "l
```

## Parcelamento pedido pelo cliente

```
Você: posso parcelar o Takamine GD20 em 10x?

Assistente: Sim, você pode parcelar o Takamine GD20 em 10x. Cada parcela seria de **R$ 219,90** sem juros. O valor total permanece **R$ 2.199,00**. 

Se quiser, também pode combinar formas de pagamento (como PIX + cartão) para compras acima de R$ 2.000,00. Precisa de ajuda para finalizar a compra? 😊

[trace] 282.2s, 2 tool call(s)
[trace]   search_products(query='Takamine GD20') -> 1 products
[trace]   quote_payment(installments=10, product_id=95) -> {"product": "Takamine GD20 Dreadnought Natural", "availability": "available", "l
[trace]   grounding: no ungrounded prices or names found
```

```
Você: e o Yamaha C40 em 6x, quanto fica?

Assistente: Parcelar o Yamaha C40 em 6x é possível! Cada parcela seria de **R$ 99,98** sem juros. O valor total permanece **R$ 599,90**. 

Se quiser, também pode pagar à vista com PIX e ganhar **R$ 30,00 de desconto** (totalizando **R$ 569,90**). Precisa de ajuda para escolher a melhor opção? 😊

[trace] 475.5s, 2 tool call(s)
[trace]   search_products(query='Yamaha C40') -> 1 products
[trace]   quote_payment(installments=6, product_id=81) -> {"product": "Yamaha C40 Nylon Natural", "availability": "available", "l
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- Conferência dos valores: PIX = 5% de R$ 2.199,00 = R$ 109,95. Parcelas = total ÷ n, arredondado para cima no centavo (274,875 → 274,88). 10x de R$ 219,90 respeita o mínimo de R$ 100,00 para 7x a 12x; 6x de R$ 99,98 respeita o de R$ 80,00 para 4x a 6x.
- Este é o caso que motivou a tool: antes dela, o agente não consultava o preço do Takamine para responder o parcelamento.
- O agente escreveu "mínimo R$ 100,00 por parcela" para todo o crédito; é o que diz a tabela da seção 3 do manual. A regra que o código aplica é a da seção 3.1 (até 3x sem mínimo, 4x a 6x com R$ 80,00), que prevalece. Aqui o resultado não muda.
- Os tempos (de 146 a 475 s) são os mais altos das conversas: as respostas encadeiam duas tools e o contexto é maior. Fica registrado como limitação.

# 01 — Catálogo e preço

Mostra o agente consultando os dados em tempo real: primeiro descobre a categoria, depois busca com o filtro de preço; no segundo turno busca um modelo pelo nome.

```
Você: Quais opções de violões disponíveis custando até R$1000?

Assistente: Tem 12 opções de violões disponíveis até R$1.000. Aqui estão os mais acessíveis:

1. **Tagima Memphis AC-39 Nylon Natural** - R$ 429,90  
2. **Rozini RC-104 Nylon Estudante** - R$ 459,90  
3. **Shelby SN-100 Folk Aço Preto** - R$ 549,00  
4. **Giannini GF-1R Aço Folk Sunburst** - R$ 579,90  
5. **Yamaha C40 Nylon Natural** - R$ 599,90  
6. **Giannini GN-15 Nylon Cedr Natural** - R$ 689,00  
7. **Yamaha F310 Aço Natural** - R$ 699,90  
8. **Tagima Dallas Tuner Aço Natural** - R$ 749,00  
9. **Shelby SGD-195E Elétrico Aço Sunburst** - R$ 799,00  
10. **Yamaha C70 Nylon Natural** - R$ 849,00  
11. **Tagima Woodstock Dreadnought Natural** - R$ 899,00  
12. **Tagima TW-7 7 Cordas Aço Natural** - R$ 999,00  

Quer refinar por cor, tipo de corda (nylon/steel) ou ver apenas os com captador?

[trace] 165.7s, 2 tool call(s)
[trace]   list_categories(query='violão') -> 9 items
[trace]   search_products(max_price=1000, sort='price_asc', category_id=5) -> 12 products
[trace]   grounding: no ungrounded prices or names found

Você: Quanto custa o Takamine GD20?

Assistente: O **Takamine GD20 Dreadnought Natural** custa **R$ 2.199,00**. É um violão dreadnought com tampo de cedro sólido, ideal para fingerstyle. Quer saber mais sobre ele ou precisa de ajuda com algo else? 😊

[trace] 96.5s, 1 tool call(s)
[trace]   search_products(query='Takamine GD20') -> 1 products
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- Os 12 produtos, os preços e a ordem (do mais barato ao mais caro) conferem com o CSV; só entram produtos ativos e com estoque.
- A tool `list_categories` recebeu um argumento `query` que ela ignora: o modelo de 8B preenche campos que não existem. O resultado não é afetado.
- "ideal para fingerstyle" vem da descrição do produto no CSV ("Excelente para fingerstyle com timbre quente e definido").
- "algo else" é uma palavra em inglês que escapou do modelo, uma falha conhecida dele.

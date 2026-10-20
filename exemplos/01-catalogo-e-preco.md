# 01 — Catálogo e preço

Consulta ao catálogo em tempo real. No primeiro turno o agente descobre a categoria e busca com o filtro de preço; no segundo busca um modelo pelo nome.

Conversa nova, com contexto zerado:

```
Você: Quais opções de violões disponíveis custando até R$1000?

Assistente: Aqui estão os violões disponíveis até R$1000, ordenados pelo preço:

1. **Tagima Memphis AC-39 Nylon Natural** - R$ 429,90  
   *Cordas de nylon, corpo leve, ideal para iniciantes.*

2. **Rozini RC-104 Nylon Estudante** - R$ 459,90  
   *Madeiras nacionais, acabamento caprichado.*

3. **Shelby SN-100 Folk Aço Preto** - R$ 549,00  
   *Versátil, bom custo-benefício.*

4. **Giannini GF-1R Aço Folk Sunburst** - R$ 579,90  
   *Tampo em Spruce, acabamento elegante.*

5. **Yamaha C40 Nylon Natural** - R$ 599,90  
   *Som equilibrado, excelente para estudantes.*

6. **Giannini GN-15 Nylon Cedr Natural** - R$ 689,00  
   *Sonoridade quente, ideal para iniciantes avançados.*

7. **Yamaha F310 Aço Natural** - R$ 699,90  
   *Um dos modelos mais vendidos do mundo.*

8. **Tagima Dallas Tuner Aço Natural** - R$ 749,00  
   *Cordas de aço, afinador integrado.*

9. **Shelby SGD-195E Elétrico Aço Sunburst** - R$ 799,00  
   *Eletroacústico com captação, bom para amplificação.*

10. **Yamaha C70 Nylon Natural** - R$ 849,00  
    *Timbre equilibrado, acabamento de alta qualidade.*

11. **Tagima Woodstock Dreadnought Natural** - R$ 899,00  
    *Som potente, ideal para fingerpicking.*

12. **Tagima TW-7 7 Cordas Aço Natural** - R$ 999,00  
    *7 cordas para projeção extra, braço confortável.*

Quer refinar por cor, tipo de corda (aço/nylon) ou outro filtro?

[trace] 113.0s, 2 tool call(s)
[trace]   list_categories(query='violão') -> 9 items
[trace]   search_products(category_id=5, max_price=1000, sort='price_asc') -> 12 products
[trace]   grounding: no ungrounded prices or names found

Você: Quanto custa o Takamine GD20?

Assistente: O **Takamine GD20 Dreadnought Natural** custa **R$ 2.199,00**. É um violão dreadnought com tampo de cedro sólido, ideal para fingerstyle. Quer saber se tem opções com desconto ou outras cores? 😊

[trace] 70.7s, 1 tool call(s)
[trace]   search_products(query='Takamine GD20', include_unavailable=True) -> 1 products
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- Os 12 produtos, os preços e a ordem (do mais barato ao mais caro) conferem com o CSV; só entram produtos ativos e com estoque. Todas as frases descritivas de cada violão vêm da descrição do produto no CSV (por exemplo, "Um dos modelos mais vendidos do mundo" é da descrição da Yamaha F310).
- A tool `list_categories` recebeu um argumento `query` que ela ignora: o modelo de 8B preenche campos que não existem. O resultado não é afetado.
- A busca do Takamine usou `include_unavailable=True` por conta própria; o produto está disponível, então o resultado é o mesmo.
- O tempo do primeiro turno (113 s) inclui duas chamadas de tool e uma resposta longa de 12 itens.

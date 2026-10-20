# 05 — Contexto, orçamento sem resultado e produto descontinuado

Conversa em três turnos. Mostra que o agente mantém o assunto ("eu tenho 1000 reais" continua falando de guitarras), diz com clareza quando não há o que foi pedido e entende que um produto descontinuado existe mas não é vendido.

```
Você: voces vendem guitarra?

Assistente: Sim, temos guitarras! No momento, temos 5 modelos disponíveis em cores como Butterscotch Blonde, Desert Sun Yellow, Eriza Verde, Heritage Cherry Sunburst e Sunburst. Qual tipo de guitarra você está procurando? Por exemplo: elétrica, acústica, eletroacústica, ou algum modelo específico?

[trace] 46.9s, 1 tool call(s)
[trace]   list_categories(query='guitarra') -> 9 items
[trace]   grounding: no ungrounded prices or names found

Você: eu tenho 1000 reais

Assistente: Não temos guitarras disponíveis até R$ 1.000 no momento. Queremos sugerir ukuleles, que são mais acessíveis e também estão disponíveis em até R$ 1.000. Tem interesse em ver opções de ukulele?

[trace] 44.5s, 1 tool call(s)
[trace]   search_products(category_id=1, max_price=1000, sort='price_asc') -> 0 products
[trace]   grounding: no ungrounded prices or names found

Você: e o Ibanez Bass 2X, tem?

Assistente: O Ibanez Bass 2X está descontinuado e não temos estoque no momento. Temos 3 modelos de baixo disponíveis no momento – quer ver opções que possam substituir? Posso mostrar as disponíveis ou ajudar com algo else? 😊

[trace] 46.6s, 1 tool call(s)
[trace]   search_products(query='Ibanez Bass 2X', include_unavailable=True) -> 1 products
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- As guitarras da loja custam de R$ 5.400,00 a R$ 18.900,00, então a busca "até R$ 1.000" na categoria 1 volta vazia (0 products) e o agente diz isso na primeira frase. Antes de uma correção no prompt, ele trocava de categoria sem avisar.
- O Ibanez Bass 2X é um produto descontinuado: o agente o encontra (`include_unavailable=True`), mas diz que não é vendido e oferece os 3 baixos disponíveis.
- Falhas do modelo visíveis: no primeiro turno ele pergunta por "acústica, eletroacústica" quando as 5 guitarras são elétricas; no segundo, afirma que os ukuleles "estão disponíveis em até R$ 1.000" sem ter feito essa busca (provavelmente é verdade, mas não foi verificado); e no último escreve "algo else". A conferência de fundamentação não pega nenhum dos três.

# 05 — Categoria sem produtos e política

A loja tem categorias sem nenhum produto (sopro, metais, cordas orquestrais). O segundo turno pergunta pela política de troca de um acessório.

Conversa nova, com contexto zerado:

```
Você: Vocês vendem saxofone?

Assistente: Aqui no Empório da Música, temos instrumentos de sopro em madeira, incluindo saxofones, mas no momento não temos modelos disponíveis para venda. Se quiser, posso te mostrar outros instrumentos da mesma categoria ou de outras categorias que temos em estoque. O que você está procurando?

[trace] 32.1s, 1 tool call(s)
[trace]   list_categories(query='saxofone') -> 9 items
[trace]   grounding: no ungrounded prices or names found

Você: a boquilha do sax pode trocar?

Assistente: Aqui no Empório da Música, **boquilhas de instrumentos de sopro não são elegíveis para troca**, por questões de higiene. Se precisar de ajuda com outro instrumento ou acessórios, posso te mostrar opções disponíveis. Quer ver algo específico? 😊  

*Para dúvidas sobre trocas ou garantia, entre em contato com a nossa equipe pelos telefones: (67) 3341-4444 ou (67) 3321-4500.*

[trace] 28.6s, 0 tool call(s)
[trace]   ALERT: 'boquilhas de instrumentos de sopro não são elegíveis para troca' was not found in the tool results or the manual
```

## Observações
- O agente não inventou saxofones nem preços, e disse que não há modelos para venda.
- **Imprecisão:** "temos instrumentos de sopro em madeira, incluindo saxofones, mas no momento não temos modelos disponíveis" soa contraditório, e "outros instrumentos da mesma categoria" não existe, porque a categoria está vazia. O modelo leu a descrição da categoria como se fosse estoque.
- A resposta sobre a boquilha está correta (o manual diz que boquilhas de instrumentos de sopro não são elegíveis para troca, por higiene). O alerta de fundamentação é um **falso positivo**: a frase em negrito é uma paráfrase do manual, e a conferência exige o texto exato.
- O agente passou os dois números de telefone como se ambos fossem para dúvidas; o segundo é o WhatsApp de atendimento.

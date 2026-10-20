# 03 — Política de devolução

Aplica a regra de arrependimento do manual (seção 4.1).

Conversa nova, com contexto zerado:

```
Você: Me arrependi da minha compra, posso devolver meu pedido?

Assistente: Claro! Se você se arrependeu da compra, pode solicitar a devolução em até 7 dias corridos após o recebimento do produto, desde que ele esteja em sua embalagem original, sem sinais de uso, com todos os acessórios e manuais. O reembolso será realizado na mesma forma de pagamento original em até 10 dias úteis. O frete da devolução é por conta da loja. Precisa de ajuda para iniciar o processo? 😊

[trace] 30.5s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- Prazo (7 dias corridos após o recebimento), condições, reembolso (até 10 dias úteis) e frete por conta da loja conferem com o manual.

- **Limitação:** o agente responde a regra geral e não consulta o pedido do cliente, então não sabe se o prazo dele ainda vale. A consulta de pedidos e a checagem de elegibilidade ficaram fora do escopo desta entrega.

# Exemplos de conversa

Cinco conversas reais com o agente, copiadas da saída do terminal (`uv run emporio --trace`), sem edição. **Cada conversa foi uma execução nova do agente, com contexto zerado**: nenhuma lembra da anterior. Cada arquivo diz o que mostra, quais tools foram chamadas e os erros que o modelo cometeu.

| Arquivo | O que mostra |
|---|---|
| [01-catalog-and-price.md](01-catalog-and-price.md) | Consulta ao catálogo em tempo real: opções até um orçamento e preço de um produto |
| [02-store-information.md](02-store-information.md) | Endereço e horário respondidos a partir do manual de políticas |
| [03-returns.md](03-returns.md) | Aplicação da política de devolução |
| [04-payment.md](04-payment.md) | Cotação de pagamento calculada pelo código: parcelas e PIX |
| [05-category-without-products.md](05-category-without-products.md) | Categoria sem produtos e uma pergunta de política |

Os testes de comportamento fora desses cenários (assuntos fora da loja, tentativas de revelar o prompt) estão em [docs/behavior-tests.md](../docs/behavior-tests.md).

**Como ler o trace:** `[trace] 46.9s, 1 tool call(s)` é o tempo da resposta e o número de tools chamadas; as linhas seguintes mostram cada chamada com os argumentos e o resumo do retorno. A última linha é a conferência de fundamentação (`--trace`): ela avisa quando a resposta cita preços ou nomes em negrito que nenhuma tool nem o manual trouxe. É uma ajuda de teste e pode errar nos dois sentidos (veja o exemplo 5).

**Configuração:** modelo de chat `qwen3:8b` e embeddings `bge-m3`, ambos locais via Ollama, em um notebook com 16 GB de memória. O tempo por resposta (de 15 a 113 s) reflete isso.

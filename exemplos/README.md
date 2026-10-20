# Exemplos de conversa

Cinco conversas reais com o agente, copiadas da saída do terminal (`uv run emporio --trace`), sem edição. Cada arquivo diz o que mostra e quais tools foram chamadas.

| Arquivo | O que mostra |
|---|---|
| [01-catalogo-e-preco.md](01-catalogo-e-preco.md) | Consulta ao catálogo em tempo real: opções até um orçamento e preço de um produto |
| [02-informacoes-da-loja.md](02-informacoes-da-loja.md) | Dados da loja respondidos a partir do manual de políticas |
| [03-devolucao.md](03-devolucao.md) | Aplicação da política de devolução e encaminhamento para a equipe |
| [04-pagamento.md](04-pagamento.md) | Cotação de pagamento calculada pelo código: PIX, débito, boleto e parcelas |
| [05-contexto-e-limites.md](05-contexto-e-limites.md) | Conversa em vários turnos: orçamento sem resultado e produto descontinuado |

**Como ler o trace:** `[trace] 46.9s, 1 tool call(s)` é o tempo da resposta e o número de tools chamadas; as linhas seguintes mostram cada chamada com os argumentos e o resumo do retorno. A última linha é a conferência de fundamentação (`--trace`): ela avisa quando a resposta cita preços ou nomes em negrito que nenhuma tool nem o manual trouxe.

**Configuração:** modelo de chat `qwen3:8b` e embeddings `bge-m3`, ambos locais via Ollama, em um notebook com 16 GB de memória. O tempo por resposta (de 45 a 280 s) reflete isso.

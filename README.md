# Empório da Música — Customer Service Agent

Customer service agent for Empório da Música, a fictional musical instruments store. The agent answers in Portuguese and queries the store data through tools. Today it handles the product catalog: types, prices, promotions, colors and availability. Orders, policies, payment and store information are being added feature by feature.

## Running the project

Requirements: [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com/) (the default model runs locally). Python 3.13 is installed by `uv` if missing.

```bash
# 1. Install the dependencies
uv sync

# 2. Download the local models and keep Ollama running
ollama pull qwen3:8b   # chat model, about 5 GB
ollama pull bge-m3     # embeddings for the store manual, about 1.2 GB

# 3. Optional: copy the settings file and adjust it (the defaults already work with Ollama)
cp .env.example .env

# 4. Chat with the agent (type "sair" to leave)
uv run emporio
```

Settings (in `.env` or the environment):

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Model provider. Only Ollama is available for now |
| `LLM_MODEL` | `qwen3:8b` | Model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is running |
| `LLM_REASONING` | `true` | Reasoning before answering. With `false` the 8B model often skips the tools |
| `OLLAMA_NUM_CTX` | `8192` | Context size in tokens |
| `EMBEDDING_MODEL` | `bge-m3` | Embeddings model for the manual search |

Add `--trace` (`uv run emporio --trace`) to see, under each answer, how long it took, which tools were called with which arguments, and a grounding check that flags prices and names the tools never returned. The check is a testing aid: it does not judge opinions or other claims.

Answers take 10 to 90 seconds with the default model on a laptop; the reasoning is what makes the tool calls reliable.

Tests and checks (no model and no network needed):

```bash
uv run pytest                        # the retrieval tests (marked integration) skip without Ollama
uv run pytest -m integration         # only the tests that need Ollama and bge-m3
uvx ruff check src tests
uvx basedpyright src tests
```

## Stack

| Topic | Decision |
|---|---|
| Approach | ReAct agent with tools; the policy RAG is one of the tools |
| Framework | LangChain, using `create_agent` (may migrate to `ToolNode` / a manual graph later) |
| RAG | Semantic search (embeddings), PDF split by section |
| Provider / model | Ollama (`qwen3:8b`, local) for development and Google Gemini (free tier) to compare, selected by environment variables |
| Architecture | Miniature layers (data/domain, agent, infrastructure/interface) |
| Language / tooling | Python 3.13, `uv` for environment and dependencies (`pyproject.toml` + `uv.lock`), `pytest` for tests, `src/` layout |
| Business rules | In code, not in the LLM |
| Only if time allows | Docker, observability (Langfuse), LLM-as-judge |

## Rules per scenario

The original CSVs are not modified; rules are applied in code.

### Products
| Scenario | Behavior |
|---|---|
| `active` and stock > 0 | Available |
| `active` and stock 0 | "Out of stock at the moment" |
| Status other than `active` (e.g. `discontinued`, `coming_soon`) | Unavailable; never offer |
| Discontinued product mentioned by the customer as a reference | May be looked up (e.g. "I bought a guitar from you, was it nylon or steel?") |
| Promotions | Only those with `is_active = 1` apply |
| `specs` column (JSON as text) | Converted into structured fields when loading the data |
| Category with no products (woodwinds, brass, orchestral strings) | Normal: there are no items yet |

### Orders
| Scenario | Behavior |
|---|---|
| `total_brl` in the CSV | It is the amount actually paid; never recalculate (orders 3 and 20 differ from the sum of their items) |
| `shipped` order whose estimated delivery has already passed (e.g. order 8) | Flag the delay |
| `pending` / `confirmed` order with no tracking code or estimated delivery | Normal |

### Dates
- "Today" is `datetime.now()`.

### Contacts
| Channel | Value |
|---|---|
| Email | contato@emporiodamusica.com.br (no accent) |
| Store phone | (67) 3341-4444 |
| Customer service WhatsApp | (67) 3321-4500 |

## Returns and exchanges

Rules come from the store manual (sections 4 and 8). The backend is the source of truth and enforces them; the agent learns what is allowed from the backend, so it never promises something that would be refused.

| Case | Deadline | Counted from |
|---|---|---|
| Regret / withdrawal (4.1) | 7 calendar days | Receipt of the product |
| Exchange for defect (4.2) | 30 calendar days | Purchase date |
| Exchange by preference (4.3) | 7 days | Not stated in the manual → treated as receipt (see gap 2) |
| Legal warranty (8.1) | 90 days | Receipt of the product |

### Known gaps and chosen solutions

1. **Receipt date does not exist in the data.** The CSVs only have `order_date` (purchase) and `estimated_delivery` (estimated, not actual).
   **Solution:** for orders with status `delivered`, `estimated_delivery` is used as the receipt date. Orders that are not `delivered` are not eligible for return or exchange.
2. **The manual does not say when the 7-day window for exchange by preference starts** (section 4.3).
   **Solution:** it is counted from receipt, like regret.

## Payment quote

`PaymentService.quote` computes the quote for a product, and the agent calls it through the `quote_payment` tool. The quote lists every option; with a number of installments it also singles out that credit card option.

| Method | Rule |
|---|---|
| PIX | 5% discount over the list price; **not applied** to promotional prices |
| Debit card, bank slip | Single payment, no discount |
| Credit card | Up to 12x without interest, following section 3.1 |

Credit card installments (section 3.1):

| Installments | Minimum installment value |
|---|---|
| Up to 3x | No minimum, but the purchase total must be at least R$ 50.00 to be split |
| 4x to 6x | R$ 80.00 |
| 7x to 12x | R$ 100.00 |

Rounding: an installment is the total divided by the number of installments, rounded half up to the cent, and that rounded value is the one compared with the minimum. Different payment methods can be combined only on purchases above R$ 2,000.00.

### Known gap and chosen solution

- **The manual contradicts itself.** The table in section 3 states a minimum installment of R$ 100.00 for any credit card purchase, while section 3.1 defines the tiers above.
  **Solution:** section 3.1 prevails, since it is the detailed rule.
- **"Except below R$ 50.00" in section 3.1 is ambiguous** (installment or total?).
  **Solution:** it is read as the purchase **total**: purchases under R$ 50.00 cannot be split.

## Architecture

Layers, principles and the decision log are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

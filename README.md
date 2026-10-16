# Empório da Música — Customer Service Agent

Project definitions agreed so far.

## Stack

| Topic | Decision |
|---|---|
| Approach | ReAct agent with tools; the policy RAG is one of the tools |
| Framework | LangChain, using `create_agent` (may migrate to `ToolNode` / a manual graph later) |
| RAG | Semantic search (embeddings), PDF split by section |
| Provider / model | Google Gemini (free tier), configurable via environment variables |
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

A backend function computes the quote for a purchase.

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

### Known gap and chosen solution

- **The manual contradicts itself.** The table in section 3 states a minimum installment of R$ 100.00 for any credit card purchase, while section 3.1 defines the tiers above.
  **Solution:** section 3.1 prevails, since it is the detailed rule.
- **"Except below R$ 50.00" in section 3.1 is ambiguous** (installment or total?).
  **Solution:** it is read as the purchase **total**: purchases under R$ 50.00 cannot be split.

## Architecture

Layers, principles and the decision log are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

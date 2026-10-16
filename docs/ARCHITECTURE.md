# Architecture

Architectural decisions for the Empório da Música customer service agent. Business rules (returns, payment, data handling) are documented in the [README](../README.md).

## Overview

```
Customer ──▶ Agent ──▶ Services (backend rules) ──▶ Data (CSV) 
                                   └──────────────▶ Policies (PDF, semantic search)
```

- The **backend** (services) is the source of truth and enforces every business rule. The agent cannot bypass it.
- The **agent** is the front end: it knows what the backend allows, so it does not promise something that would be refused.
- Nothing in the backend depends on the agent. The backend can be tested with no LLM and no network.

## Layers

Planned layout under `src/emporio/`. Each folder is created by the first feature that needs it.

| Layer | Responsibility | May depend on |
|---|---|---|
| `domain/` | Pydantic models, enums (e.g. product availability), domain errors with stable reason codes | Standard library and Pydantic |
| `data/` | Loads the CSVs and builds the domain models, which validate and convert each row; converts `specs`, parses dates, keeps only active promotions | `domain` |
| `services/` | Business rules, one module per feature | `domain`, `data` |
| agent (later) | Tools over the services, prompt, `create_agent` | `services` |
| interface (later) | Entry point used to talk to the agent | agent |

Dependencies point down: a layer never imports from a layer above it.

### Domain modules

`domain/` has one module per subject, named after the service that uses it (`domain/pricing.py` ↔ `services/pricing.py`), instead of a single `models.py` that would grow with every feature.

| Module | Contents |
|---|---|
| `catalog.py` | `Product`, `ProductStatus` |
| `pricing.py` | `Promotion`, `PriceBreakdown` |
| `money.py` | Rounding helper for BRL amounts |
| `errors.py` | `ErrorCode`, `DomainError` and its subclasses |

New modules are added with the feature that needs them (for example `orders.py`, `customers.py`, `returns.py`, `payment.py`, `store.py`).

- A module may import from another only in one direction; no circular imports. For example, a future `orders.py` may import `catalog.py`, never the other way around.
- Request and response models that belong to one service (such as the filters and result of the product search) live next to that service, not in `domain/`.

## Principles

1. **One source of truth.** Each rule lives only in the backend. The agent learns about a rule through the backend functions, not through numbers copied into the prompt.
2. **Check before acting.** The agent asks the backend whether something is allowed before offering it; the backend also refuses invalid requests, so a mistake by the agent cannot produce a wrong outcome.
3. **Query-only backend.** It reads data and applies rules, but never writes. When an action is needed (e.g. starting a return), the customer is redirected to the store team.
4. **Injectable clock.** Anything that depends on the current time (delay detection, return deadlines, opening hours) receives the time through a clock. It defaults to `datetime.now()`; tests pass fixed dates.
5. **Structured results.** Services return data, never formatted text.
6. **Two access levels.**
   - Public (anyone, registered or not): catalog, prices, promotions, policies, store information.
   - Identified customer: orders and return eligibility, restricted to the customer's own orders.
7. **Identity by contact.** A customer is identified by email or phone (normalized). An unknown contact gets a neutral answer that does not reveal whether it exists in the data.

## Decision log

| Decision | Choice | Alternatives considered | Why |
|---|---|---|---|
| Agent approach | ReAct with tool calling; the policy RAG is one of the tools | Context stuffing, RAG only, SQL agent | The task is routing between exact data (prices, stock, orders) and free text (policies) |
| Agent framework | LangChain `create_agent` | `ToolNode` with LangGraph, manual LangGraph graph | Least code for a prototype; migration to `ToolNode` or a manual graph stays possible if more control is needed |
| Policy retrieval | Semantic search (embeddings), PDF split by numbered section | BM25 keyword search | Customers write informally ("I want my money back"); each manual section is a complete unit of meaning |
| LLM provider | Google Gemini free tier, configured by environment variables | Groq, Claude Haiku 5.5 (paid API), local models | No cost; free-tier limits change often, so provider and model are configurable |
| Where rules live | Backend code | LLM prompt | Rules with numbers (prices, deadlines) must be deterministic and testable |
| Domain models | Pydantic models, used for validation, domain representation and tool schemas | Standard library `dataclass`, `pandas`; Pydantic only at the boundaries | The CSVs arrive as text, so validation and type conversion are needed anyway; one model type avoids a raw model plus a domain model and the conversion between them. Pydantic is already required by LangChain and is the de facto standard for data validation in Python. Trade-off: the domain depends on an external library instead of the standard library alone |
| Error handling | Domain exceptions with a stable reason code | Result objects | Idiomatic Python; keeps functions simple; a higher layer can convert exceptions into structured replies |
| Backend scope | Query-only | Write operations (e.g. registering a return request) | The challenge asks to apply policies, not to execute actions; can be revisited |
| Environment | Python 3.13, `uv` (`pyproject.toml` + `uv.lock`), `pytest`, `src/` layout | `venv` + `pip` | The lock file pins every version, which matters because LangChain changes quickly |
| Time | `datetime.now()` as "today", through an injectable clock | A fixed reference date | Behaves like production; the clock keeps tests deterministic |
| Several active promotions on one product | The highest discount applies; the lowest promotion id breaks ties | Stacking them | The manual says promotions are not cumulative; the tie-break keeps the result independent of CSV row order |
| Money | `Decimal`, rounded half up to the cent | `float`, banker's rounding | Floats cannot represent prices exactly; half up is what a customer expects (1.005 becomes 1.01) |
| Promotion name | The promotion `description` from the data | A separate name field | The data has no separate name column |

## Only if time allows

Docker, observability with Langfuse, and LLM-as-judge evaluation.

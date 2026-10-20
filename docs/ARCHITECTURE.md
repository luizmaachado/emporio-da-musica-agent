# Architecture

Architectural decisions for the Empório da Música customer service agent. Business rules (payment, data handling, and the design of returns) are documented in the [README](../README.md).

## Overview

```
Customer ──▶ Agent ──┬──▶ Tools ──▶ Services (backend rules) ──▶ Data (CSV)
                     └──▶ Manual retrieval (PDF, semantic search), added to the prompt
```

- The **backend** (services) is the source of truth and enforces every business rule. The agent cannot bypass it.
- The **agent** is the front end: it knows what the backend allows, so it does not promise something that would be refused.
- Nothing in the backend depends on the agent. The backend can be tested with no LLM and no network.

## Layers

Layout under `src/emporio/`.

| Layer | Responsibility | May depend on |
|---|---|---|
| `domain/` | Pydantic models, enums (e.g. product availability), domain errors with stable reason codes | Standard library and Pydantic |
| `data/` | Loads the CSVs and reads the manual (PDF) into sections, and builds the domain models, which validate and convert each row; converts `specs`, parses dates, keeps only active promotions | `domain` |
| `services/` | Business rules, one module per feature | `domain`, `data` |
| `agent/` | `tools.py` (thin wrappers over the services), `prompt.py`, `llm.py` (model from environment variables), `agent.py` (composition root: loads the data, builds the services and `create_agent`), `policies.py` (retrieval over the store manual), `trace.py` and `grounding.py` (testing aids, see the decision log), `messages.py` (reads message text) | `services`, `data`, `domain` |
| `cli.py` | Chat loop used to talk to the agent (`uv run emporio`); `--trace` shows time, tool calls and the grounding check under each answer | `agent` |

Dependencies point down: a layer never imports from a layer above it.

### Domain modules

`domain/` has one module per subject, named after the service that uses it (`domain/pricing.py` ↔ `services/pricing.py`), instead of a single `models.py` that would grow with every feature.

| Module | Contents |
|---|---|
| `catalog.py` | `Product`, `ProductStatus`, `Availability`, `Category` |
| `policies.py` | `PolicySection`, one numbered section of the store manual |
| `payment.py` | `PaymentOption`, `PaymentQuote`, `PaymentMethod`, `PaymentRefusal` |
| `pricing.py` | `Promotion`, `PriceBreakdown` |
| `money.py` | Rounding helper for BRL amounts |
| `text.py` | Text normalization (case and accents) for matching what customers type |
| `errors.py` | `ErrorCode`, `DomainError` and its subclasses |

- A module may import from another only in one direction; no circular imports.
- Request and response models that belong to one service (such as the filters and result of the product search) live next to that service, not in `domain/`.

## Principles

1. **Computed rules live in the backend.** Availability, promotions, PIX and installments are computed by services, not by the model and not by numbers copied into the prompt. The rules written as prose in the manual reach the agent as text (see the decision log).
2. **Check before acting.** The agent asks the backend (through a tool) before it offers something; the backend also refuses invalid requests, so a mistake by the agent cannot produce a wrong outcome.
3. **Query-only backend.** It reads data and applies rules, but never writes. When an action is needed (e.g. starting a return), the customer is redirected to the store team.
4. **Structured results.** Services return data, never formatted text. Formatting is done in the agent layer.

## Decision log

| Decision | Choice | Alternatives considered | Why |
|---|---|---|---|
| Agent approach | ReAct with tool calling for exact data; the store manual is retrieved automatically on every turn | Context stuffing, RAG only, SQL agent | The task is routing between exact data (prices, stock, installments) and free text (policies) |
| Agent framework | LangChain `create_agent` | `ToolNode` with LangGraph, manual LangGraph graph | Least code for a prototype; migration to `ToolNode` or a manual graph stays possible if more control is needed |
| LLM provider | Ollama with `qwen3:8b`, selected by environment variables (`LLM_PROVIDER`, `LLM_MODEL`); only Ollama is implemented | Gemini free tier, Claude (paid API); neither was tried | Free, offline, and nothing leaves the machine. Local models are weaker at tool calling, which shows in the examples |
| Ollama settings | Reasoning on (`LLM_REASONING`) and a context of 8192 tokens (`OLLAMA_NUM_CTX`) | Reasoning off | With reasoning off the 8B model often skipped the tools and invented answers; the price is from about 15 s to two minutes per answer |
| Tool results | Compact data with money already formatted ("R$ 1.299,90"), domain errors returned as `{error, message}`, and the `filters` that were applied; no instructions inside the results | Raw service models; raising exceptions; notes in the results telling the model what to do | The model should not format money or crash on a refused request. Instruction notes inside results were tried first and removed: behavior belongs in the prompt, and the empty-result note led the agent to switch category silently. Formatting lives in the agent layer, services still return `Decimal` |
| Search flow | A model or brand goes in `query` only; an instrument type goes through `list_categories` and then `category_id` | Text search for everything | Text search misses plurals ("violão" vs "Violões"); the prompt carries the routing and each tool parameter says when to use it |
| Store rules and information | The manual (PDF) is the source for address, contacts, hours, payment, returns, shipping, warranty and promotions: `data/policies.py` splits it into numbered sections (`pdfplumber`, regex on the numbered titles, page headers and footers removed) and `agent/policies.py` embeds them with `bge-m3` on Ollama. Sections 7.2 (service flow, already in the prompt) and 10 (closing notes) are left out, by number | Structured `store.json` or code constants; copying the rules into the prompt | Updating the PDF updates the agent, as long as the numbering of the left-out sections holds: a test fails if 7.2 and 10 stop having the expected titles. Trade-off: opening hours, holidays and special dates are prose, so the agent answers with the opening hours and open days and does not say whether the store is open right now (it has no clock); the manual has two phone numbers, which the prompt tells apart |
| Manual retrieval | Automatic on every turn, not a tool, and with no similarity cutoff: the 3 closest sections go into that turn's system prompt | A `search_policies` tool the model decides to call; a cutoff on the similarity score | The 8B model skips tools too often. A cutoff was tried and dropped: on new questions it blocked ones it should have answered (for example "what is your CNPJ?"), while the extra sections never made the product answers worse. The manual is small, so 3 extra sections per turn cost little. `tests/agent/test_policy_retrieval_eval.py` checks 38 questions (right section in the top 3 for 37) |
| Manual in answers | The model speaks as the store and never mentions the manual or section numbers | Citing the section | Customers do not have the internal manual |
| Payment quote | `services/payment.py` holds the rules (PIX 5% but not on promotional prices, installments by tier from section 3.1, nothing is split under R$ 50.00, methods can be combined above R$ 2,000.00); the `quote_payment` tool takes a product id and optionally a number of installments and returns the amounts already formatted | Letting the model read the rule from the manual and do the arithmetic | The 8B model did not look up the price and miscounts; the code answers "can I split the Takamine in 10x?" the same way every time. An installment is the total divided by the count, rounded half up to the cent, and that rounded value is compared with the minimum. Section 3.1 wins over the table in section 3 (see the README) |
| Prompt style | The prompt says what to do, with a ready-made answer for refusals (revealing the instructions, subjects outside the store), a path per kind of request, and no field names or internal labels in answers | Prohibitions ("never..."), quoting the phrase to avoid | The 8B model ignored "never use emojis" and repeated a quoted forbidden phrase; ready-made answers stopped the prompt from being printed (except when asked in English). The rule that a category description is not stock came from a wrong answer about saxophones. Results in `docs/behavior-tests.md` |
| Grounding check | After each answer, `grounding.py` checks that every price and every **bold** name appears in a tool result of the conversation or in the manual (an amount the customer wrote also counts); `--trace` prints the alerts | An LLM judge; no check | It is cheap, deterministic and needs no model. It caught an agent answering about a product without searching. It is a manual-testing aid, not a guarantee: it can raise a false alert when a bold phrase paraphrases the manual, it does not check opinions, colors, stock or percentages, a price the model computes itself is reported, a price bound sent to a tool counts as evidence, and short bold fragments match by substring |
| Conversation memory | `InMemorySaver`, one `thread_id` per CLI run | A database | Enough for a prototype; the history is lost when the program exits |
| Domain models | Pydantic models, used for validation, domain representation and tool schemas | Standard library `dataclass`, `pandas`; Pydantic only at the boundaries | The CSVs arrive as text, so validation and type conversion are needed anyway; one model type avoids a raw model plus a domain model and the conversion between them. Pydantic is already required by LangChain and is the de facto standard for data validation in Python. Trade-off: the domain depends on an external library instead of the standard library alone |
| Error handling | Domain exceptions with a stable reason code | Result objects | Idiomatic Python; keeps functions simple; a higher layer can convert exceptions into structured replies |
| Backend scope | Query-only | Write operations (e.g. registering a return request) | The challenge asks to apply policies, not to execute actions |
| Environment | Python 3.13, `uv` (`pyproject.toml` + `uv.lock`), `pytest`, `src/` layout | `venv` + `pip` | The lock file pins every version, which matters because LangChain changes quickly |
| Several active promotions on one product | The highest discount applies; the lowest promotion id breaks ties | Stacking them | The manual says promotions are not cumulative; the tie-break keeps the result independent of CSV row order |
| Money | `Decimal`, rounded half up to the cent | `float`, banker's rounding | Floats cannot represent prices exactly; half up is what a customer expects (1.005 becomes 1.01) |
| Product search | Text search (name, description, category name) plus filters, sorted by final price, no pagination; the agent filters by category id instead of relying on text for plurals ("violão" vs "violões") | Stemming; a paginated result | The catalog has 65 products, so one answer holds them all; a category filter is exact where text matching is fragile |
| Color names | Only translations are merged (`Preto` becomes `Black`), in the loader; the filter is an exact match | Mapping every color to a base color; editing the CSV | `Red` and `Wine Red` are different colors of an instrument; the CSV stays untouched |
| Promotion name | The promotion `description` from the data | A separate name field | The data has no separate name column |

## Designed, not implemented

These were part of the design but are outside this delivery (the README lists them under "With more time"):

- **Orders and returns.** Looking up an order and checking return eligibility in code. They need two access levels (public data for anyone; orders only for an identified customer and only their own) and an identity taken from the session, never from an argument the model fills. A customer would be identified by e-mail or phone, with a neutral answer when the contact is not found.
- **A clock.** Anything that depends on the current time (delay detection, return deadlines, opening hours) would receive the time through an injectable clock, defaulting to `datetime.now()` and fixed in tests. Nothing in the code depends on the time today.

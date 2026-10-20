# Empório da Música — Customer Service Agent

A text agent for the customer service of Empório da Música, a fictional musical instruments store in Campo Grande/MS. It answers in Portuguese, in the informal-but-professional tone the store manual asks for, using the store data (CSV files) and the store manual (PDF).

**What it does today**

| Topic | How it is answered |
|---|---|
| Catalog: types, prices, promotions, colors, availability | Tools over the product CSVs (`search_products`, `list_categories`) |
| Payment: PIX, debit, bank slip, installments | Tool `quote_payment`, with the rules in code |
| Store information, opening hours, payment rules, returns, shipping, warranty, promotions | Sections of the store manual added to the prompt on every turn (semantic search) |
| Questions outside the store's scope (accessories, other subjects) | Redirected to the store's subjects, as the manual asks; not always reliably (see [behavior tests](docs/behavior-tests.md)) |

**What it does not do:** look up orders, check whether a specific order can be returned, or know whether the store is open right now. For those it explains the rule or the opening hours and sends the customer to the store team. See the [limitations](#known-limitations) and [what I would do with more time](#with-more-time).

Real conversations are in [`exemplos/`](exemplos/README.md).

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
| `LLM_PROVIDER` | `ollama` | Model provider. Only Ollama is implemented |
| `LLM_MODEL` | `qwen3:8b` | Model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is running |
| `LLM_REASONING` | `true` | Reasoning before answering. With `false` the 8B model often skips the tools |
| `OLLAMA_NUM_CTX` | `8192` | Context size in tokens |
| `EMBEDDING_MODEL` | `bge-m3` | Embeddings model for the manual search |

Add `--trace` (`uv run emporio --trace`) to see, under each answer, how long it took, which tools were called with which arguments, and a grounding check that flags prices and names the tools never returned. The check is a testing aid: it does not judge opinions or other claims.

Answers take from about 15 s to two minutes with the default model on a laptop with 16 GB (see the limitations); the reasoning is what makes the tool calls reliable.

Tests and checks (no model and no network needed):

```bash
uv run pytest                        # the retrieval tests (marked integration) skip without Ollama
uv run pytest -m integration         # only the tests that need Ollama and bge-m3
uvx ruff check src tests
uvx basedpyright src tests
```

## How it works

```
Customer message
      │
      ▼
 System prompt for this turn = fixed prompt
                              + the 3 manual sections closest in meaning to the last messages
      │
      ▼
 ReAct agent (LangChain create_agent, qwen3:8b on Ollama)
      │   decides which tools to call
      ├──▶ list_categories / search_products ──▶ ProductSearchService ──▶ CSV data + pricing rules
      └──▶ quote_payment ───────────────────────▶ PaymentService ───────▶ pricing + payment rules
      │
      ▼
 Answer (+ with --trace: time, tool calls, grounding check)
```

- **Backend (services):** pure Python, no LLM and no network. It enforces every rule (availability, promotions, installments) and returns structured data. Everything is query-only.
- **Agent:** prompt, tools (thin wrappers that format money and return facts) and the retrieval of the manual. Layers and principles are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Interface:** a command line chat. The conversation history is kept in memory, per run.

## Project layout

```
src/emporio/
  domain/     Pydantic models, enums and errors (catalog, pricing, payment, policies)
  data/       Loads the CSV files and reads the manual (PDF) into sections
  services/   The rules: pricing, product search, payment quote (no LLM, no network)
  agent/      Prompt, tools, model, retrieval of the manual, trace and grounding check
  cli.py      The chat: uv run emporio
tests/        Mirrors src/ (domain, data, services, agent)
data/         The store's CSV files and the manual, never modified
docs/         ARCHITECTURE.md (layers, principles, decision log) and behavior-tests.md
exemplos/     Five real conversations
```

## Technical decisions

Each decision has the alternatives considered in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The short version:

| Decision | Choice | Why |
|---|---|---|
| Approach | ReAct agent with tools for exact data; the manual is retrieved automatically | The task mixes exact data (prices, stock), computed rules (installments) and free text (policies). Each kind goes where it is reliable |
| Framework | LangChain `create_agent` | Least code for a prototype; tools, memory and the per-turn prompt (`dynamic_prompt`) come ready |
| Model | `qwen3:8b` on Ollama, local | Free, offline, nothing leaves the machine. Its limits are listed under the limitations |
| Rules in code, not in the prompt | Availability, promotions, PIX and installments are computed by the services | A small model skips steps and miscounts. Before `quote_payment`, asking to split the Takamine in 10x made the agent ask the customer for the price |
| Manual search | Sections split by their numbers, embedded with `bge-m3` (Ollama), the 3 closest added to the prompt on every turn | The manual is short and structured, so one chunk per section keeps each rule together. It is automatic and not a tool because the 8B model skips tools too often; no similarity cutoff because one was tried and blocked valid questions |
| PDF reading | `pdfplumber` | Keeps each table row on one line; the faster `pymupdf` split table cells |
| Prompt | One system prompt in Portuguese, rebuilt on every turn: persona and tone from the manual, a path for each kind of request (a model name, an instrument type, a payment question), the scope, and a few fixed rules. Rules are written as what to do, with a ready-made answer for refusals | Prohibitions were not followed by the 8B model: "never use emojis" was ignored in almost every answer, and naming a forbidden phrase made it appear. A positive path with a ready answer worked (revealing the prompt, empty categories). The emoji rule was dropped because it did not work |
| Product search | Text match on name, description and category, plus filters; the agent filters by category id for instrument types | Plain text misses plurals ("violão" does not match "Violões"); the category id is exact |
| Colors | Only translations are merged (`Preto` becomes `Black`) | `Red` and `Wine Red` are different colors of an instrument |
| Checks of the answers | `--trace` and a grounding check (every price and **bold** name must come from a tool result or the manual) | A cheap, deterministic way to see wrong answers while testing. It is not a guarantee |
| Tool results | Facts only, plus the filters that were applied | Instructions inside results made the agent change category silently; behavior belongs in the prompt |
| Persistence | None beyond the run | The CLI is a single conversation; it was enough for the prototype |

### How the answers were evaluated

- **Backend:** unit tests with synthetic data and with the real CSVs (`uv run pytest`, 180 tests).
- **Manual search:** 38 questions with the section that should answer them; the right section is in the top 3 for 37 and first for most (`tests/agent/test_policy_retrieval_eval.py`, needs Ollama).
- **The agent itself:** by hand, with `--trace`, comparing each answer with the data. Language models are not deterministic, so there is no automated test of the final text. The examples in `exemplos/` include the mistakes that were seen, and [docs/behavior-tests.md](docs/behavior-tests.md) records questions outside the store's scope and attempts to make the agent reveal its instructions.

## Data handling

The original CSV files and the PDF are never modified; rules are applied in code.

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

### Contacts
| Channel | Value |
|---|---|
| Email | contato@emporiodamusica.com.br (no accent) |
| Store phone | (67) 3341-4444 |
| Customer service WhatsApp | (67) 3321-4500 |

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

## Returns and exchanges (designed, not implemented)

The agent explains the rules of the manual (sections 4 and 8) but does not check a specific order. Design for that feature:

| Case | Deadline | Counted from |
|---|---|---|
| Regret / withdrawal (4.1) | 7 calendar days | Receipt of the product |
| Exchange for defect (4.2) | 30 calendar days | Purchase date |
| Exchange by preference (4.3) | 7 days | Receipt (the manual does not say; assumed like regret) |
| Legal warranty (8.1) | 90 days | Receipt of the product |

The data has no receipt date, so for `delivered` orders `estimated_delivery` stands in for it, and orders in any other status are not eligible.

## Assumptions about the sources

The manual and the data contradict themselves in a few places. These are the choices made, so the answers are consistent:

| Source | Problem | Choice |
|---|---|---|
| Manual | Two phone numbers: section 1.2 gives (67) 3341-4444 as phone and WhatsApp, section 7 gives (67) 3321-4500 as the WhatsApp line | (67) 3341-4444 is the store phone and (67) 3321-4500 is the customer service WhatsApp; the prompt tells them apart |
| Manual | The e-mail is written with an accent (`empóriodamusica`) | Without accent, the only form that works |
| Manual | Payment table says a minimum installment of R$ 100.00 for any credit purchase; section 3.1 defines tiers | Section 3.1 prevails (see [Payment quote](#payment-quote)) |
| Manual | "Over 300 instruments"; the CSV has 65 products | The agent never states a total; the data is the source |
| Manual | Holidays and special dates are described in prose only | The agent answers with the regular opening hours |
| Manual | Section 4.3 does not say when the 7 days for an exchange by preference start | From receipt, like regret |
| Data | No receipt date for orders | `estimated_delivery` as the receipt date, in the returns design |

## Known limitations

- **Model.** Accuracy and speed are bounded by the local 8B model (15 s to 113 s per answer; invented details, instructions that are sometimes ignored: see [`exemplos/`](exemplos/README.md) and [docs/behavior-tests.md](docs/behavior-tests.md)). The model is a setting. What must not depend on it, prices, installments and availability, is computed in code.
- **Orders and returns are not built.** No customer identification, order status or return eligibility check; the agent explains the rule and sends the customer to the store contacts. For the same reason it greets by name only when the customer gives one.
- **No clock.** It cannot say whether the store is open now.
- **Coverage of the checks.** Text search misses products that never name their instrument type (the Martin D-28E never says "violão"), which the category filter covers for instrument types. Manual retrieval was checked on 38 questions I wrote and has no reranker. The grounding check is a testing aid that covers prices and bold names only.
- **One provider, in-memory history.** Only Ollama was implemented and measured, and the conversation is lost when the program exits.

## With more time

1. **Orders and returns.** Three services written in code and tested with a fixed clock: `identify(contact)` (answers the same way whether or not the contact exists), `list_orders(customer)` and `check_return_eligibility(order, reason, today)`, using the deadlines above. The customer identity would live in the run state and never in an argument the model fills. These flows need a fixed order of steps (identify, find the order, check in code, answer), which the local 8B model chains slowly and unreliably, so I would write them as an explicit LangGraph graph (`create_agent` already runs on LangGraph) and keep the free-form agent for the catalog and the manual.
2. Compare other models (Gemini free tier, Claude) on the same questions.
3. Automated evaluation of the final answers: an LLM as judge over questions with the facts each answer must contain.
4. **Observability with [Langfuse](https://langfuse.com/docs/langchain).** `--trace` shows each turn but stores nothing. Langfuse plugs into LangChain through a callback handler passed in the `config` that `cli.py` already builds, so the agent code would not change, and would keep every conversation as a trace (the retrieved manual sections, each tool call and its time) to find slow or wrong turns. Left out because it needs an extra service; self-hosting would be the choice, since the traces hold customers' messages.
5. A clock for opening hours, and holidays and special dates in the data.
6. Cached embeddings, streaming answers, a Docker image and a web interface.

## Use of code assistants

I built this project with **Claude Code**. How I used it:

- **Decisions first.** For each feature we discussed the options and trade-offs in the conversation (for example: structured store data versus retrieval from the manual, a tool versus automatic retrieval, which PDF library) and I made the call before any code was written. The reasoning is recorded in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Small features, small commits.** One branch and pull request per feature, with atomic Conventional Commits that I asked for explicitly; the assistant never committed on its own. Each commit leaves the test suite passing.
- **Tests with the code.** Business rules were written with their tests (boundaries of the installment rules, the manual parser, retrieval).
- **Three read-only review agents** defined in [`.claude/agents/`](.claude/agents): `architecture-reviewer` (checks the code against the documented architecture and rules), `code-reviewer` (correctness, readability and test quality) and `commit-planner` (proposes how to split the changes into commits). They ran before most merges, and I decided which findings to apply.
- **Research and measurement, not guesses.** When a choice was in doubt we measured it: PDF readers compared on the real manual, retrieval checked with questions that were not used to tune it, and the retrieval cutoff dropped after a side-by-side run showed it blocked valid questions.
- **Manual testing of the agent** with `--trace`, reading each answer against the data. The conversations in `exemplos/` are copied from the terminal without editing.

## Architecture

Layers, principles and the decision log are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

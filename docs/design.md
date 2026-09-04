# Design: Pagila Customer Support Assistant

## 1. Overview

This project is a customer-support assistant built on the OpenAI Agents SDK,
backed by the Pagila PostgreSQL sample database. A FastAPI endpoint accepts a
customer message, routes it through a triage agent to a specialist agent, and
returns a structured response with the answer, routing decision, tools used,
and citations.

## 2. Architecture

Client
|
v
FastAPI (app/main.py) - POST /agent/respond
|
v
handle_customer_request() (app/main.py)
|
v
TriageAgent --handoff--> {CatalogAgent | SubscriptionAgent |
RentalHistoryAgent | KnowledgeAgent |
HumanHandoffAgent}
|
v
Specialist agent calls a database-backed or mock tool (app/tools/)
|
v
output_guardrail (GuardrailReview agent) reviews the response
|
v
FinalAnswer -> AgentResponse (FastAPI)

Module layout (split by responsibility rather than one monolithic file):

app/
├── database.py       # SQLAlchemy engine, loaded once
├── models.py         # Shared dataclasses/Pydantic models + MODEL_CHOICE
├── main.py           # FastAPI app, orchestration (handle_customer_request)
├── tools/            # One file per database-backed or mock tool
├── guardrails/       # output_guardrail.py
├── agents/           # One file per Agent + hooks.py
├── mcp/              # metadata.py, server.py, run_server.py
├── evals/            # evals.md, structured eval cases
└── docs/             # design.md, implementation_plan.md, ai_usage.md


Supporting pieces:
- `app/database.py`: loads `.env`, builds the SQLAlchemy `engine` from
  `DATABASE_URL`, and prints a connectivity check on import.
- `alembic.ini` + `migrations/versions/`: schema migrations against the
  Pagila database (baseline, `film.streaming_available` column,
  `streaming_subscription` table).
- `app/mcp/server.py`: `LocalPagilaSupportMCPServer`, an MCP-shaped local
  adapter (`pagila-support-mcp`) exposing the same tools outside the agent
  runtime.

## 3. Agents and routing

Routing uses the SDK's native `handoffs` mechanism (not custom if/else
dispatch). Each specialist agent lives in its own module under `app/agents/`
and is assembled into `triage_agent` (`app/agents/triage_agent.py`).
`triage_agent` calls `record_triage` (`app/tools/triage.py`) — recording
`intent` and `confidence` onto `SupportContext` — and then hands off to
exactly one specialist:

| Agent | Module | Handles | Intent value | Tool(s) |
|---|---|---|---|---|
| `CatalogAgent` | `app/agents/catalog_agent.py` | film/category/rating/price/streaming questions | `catalog_search` | `search_film_catalog` |
| `SubscriptionAgent` | `app/agents/subscription_agent.py` | subscription plan/status/renewal | `subscription_question` | `get_customer_streaming_subscription` |
| `RentalHistoryAgent` | `app/agents/rental_history_agent.py` | recent rentals | `rental_history` | `get_customer_rental_history` |
| `KnowledgeAgent` | `app/agents/knowledge_agent.py` | general support/FAQ, refunds, payment-method/billing questions | `knowledge_question` | `search_kb` |
| `HumanHandoffAgent` | `app/agents/human_handoff_agent.py` | escalations, risky/ambiguous requests | `human_handoff` | `create_handoff_ticket` |

The `intent` values are enforced by a `Literal[...]` type on `record_triage`
(`app/tools/triage.py`), so the model cannot record an intent outside this
fixed set.

Because the SDK completes the run on the specialist agent (not back on
`TriageAgent`), `result.last_agent` and `SupportContext` (not
`result.first_output`) are the sources of truth for `selected_agent`,
`intent`, `confidence`, `tools_used`, and `citations`. This logic lives in
`handle_customer_request` in `app/main.py`.

## 4. Context propagation

A single `SupportContext` dataclass (`app/models.py`: customer_id,
conversation_id, used_tools, citations, intent, confidence) is created once
per request in `handle_customer_request` and threaded through the entire run
via `Runner.run(..., context=context)`. Tools receive it as
`RunContextWrapper[SupportContext]` and read `customer_id`/`conversation_id`
from trusted context fields — never from model-supplied arguments. This is
the ownership boundary that prevents a compromised or hallucinating model
from acting on a different customer's data.

`SupportRunHooks.on_tool_start` (`app/agents/hooks.py`) observes every tool
invocation and appends to `used_tools`/`citations` on the shared context,
giving the API a real (non-static) trail of what was used to answer the
request.

## 5. Tool boundaries

Each tool is a `@function_tool` in its own module under `app/tools/`, wraps a
real SQLAlchemy query (or a small mock for `search_kb` / `create_handoff_ticket`),
and:
- times execution and logs a structured `ToolCallLog` (conversation_id,
  tool_name, status, latency_ms, error) via `log_tool_call`
  (`app/tools/logging.py`).
- raises `ToolExecutionError` (`app/models.py`) on failure, so the FastAPI
  layer never leaks raw database exceptions to the client.

Database-backed tools:
- `search_film_catalog(query)` (`app/tools/catalog.py`) — reads `film`,
  `film_category`, `category`. Public input: free-text `query`. No customer
  data.
- `get_customer_streaming_subscription()` (`app/tools/subscription.py`) —
  reads `streaming_subscription`. No caller-supplied arguments;
  `customer_id` comes only from `SupportContext`.
- `get_customer_rental_history()` (`app/tools/rentals.py`) — joins `rental`,
  `inventory`, `film`. Same customer-scoping rule as above.

Non-database tools: `search_kb` (`app/tools/knowledge_base.py`, mock KB
lookup covering refunds, payment-method updates, and a general fallback) and
`create_handoff_ticket` (`app/tools/escalation.py`, mock ticket creation),
plus the internal `record_triage` routing tool (`app/tools/triage.py`).

## 6. Database access

All database access goes through the shared SQLAlchemy `engine`
(`app/database.py`), using `engine.connect()` + parameterized `text(...)`
queries (never string-interpolated SQL) and `result.mappings()` for
column-name access. Schema changes are made exclusively through Alembic
migrations, not by hand-editing the Pagila schema:

- `a0ad47384753` — baseline Pagila schema import.
- `e4432b255bb1` — adds `film.streaming_available BOOLEAN NOT NULL DEFAULT FALSE`.
- `96fadc45df62` — creates `streaming_subscription` and seeds a row for
  `customer_id=1` so the demo has data to return.

## 7. MCP readiness

`MCP_TOOL_METADATA` (`app/mcp/metadata.py`) declares each tool's public
contract as a `ToolSpec` (`app/models.py`): name, description, JSON
input/output schema, error behavior, auth requirement, and an explicit
ownership boundary string. This metadata deliberately excludes
`customer_id`/`conversation_id` from tool input schemas — those are
adapter-owned, not model-controlled.

`LocalPagilaSupportMCPServer` (`app/mcp/server.py`,
`server_name = "pagila-support-mcp"`) is a clean, in-process adapter:
- `list_tools()` returns MCP-shaped tool descriptors (`inputSchema`,
  `outputSchema`, `errorBehavior`, `authRequired`, `ownershipBoundary`).
- `call_tool(name, arguments, *, customer_id, conversation_id)` builds a
  fresh `SupportContext` and a `ToolContext` (the SDK's required invocation
  context, not a plain `RunContextWrapper` — a plain `RunContextWrapper`
  raises `AttributeError` on `tool_name`/`run_config` inside the SDK), then
  calls `FunctionTool.on_invoke_tool(...)` — the actual SDK-supported
  invocation surface.
- `app/mcp/run_server.py` is a runnable smoke-test entry point
  (`python -m app.mcp.run_server`) that lists all tools and exercises two
  database-backed tools end-to-end.

This adapter is intentionally not yet a network MCP transport. It can be
wrapped by `MCPServerStdio` / `MCPServerStreamableHttp` / `MCPServerSse`
later without touching tool logic, because `list_tools`/`call_tool` already
mirror MCP's `tools/list`/`tools/call` shape.

## 8. Guardrails

`support_output_guardrail` (`app/guardrails/output_guardrail.py`) is an
`@output_guardrail` attached to every specialist agent. It runs a second,
smaller `guardrail_agent` over the draft output and returns
`GuardrailFunctionOutput(tripwire_triggered=...)` based on a structured
`GuardrailDecision(blocked, reason)` (`app/models.py`). If tripped, the SDK
raises `OutputGuardrailTripwireTriggered`, which `app/main.py` catches and
converts into a safe, generic `AgentResponse`
(`next_action="response_withheld"`) instead of a 500 error.

## 9. Evaluation

`app/evals/evals.md` documents 10 structured cases (prompt, expected intent,
expected agent, expected tool, must-include/must-not-include terms, and
safety behavior), covering normal routing for all five agents plus adversarial
cases (prompt injection targeting the system prompt) and resilience cases
(nonexistent customer id) that must degrade gracefully instead of crashing or
leaking data.

## 10. Tradeoffs and known limitations

- **In-process MCP adapter, not a real transport.** Chosen for minimal
  surface area and to avoid depending on network/stdio plumbing that
  wasn't required by the assignment; it is designed to be swapped for a
  real `MCPServer*` implementation with no change to tool logic.
- **Mock KB and ticketing.** `search_kb` and `create_handoff_ticket` are not
  backed by real tables; they exist to demonstrate multi-tool routing and
  escalation without expanding schema scope.
- **Single hardcoded seed customer** (`customer_id=1`) in the
  `streaming_subscription` migration — sufficient for demoing the
  subscription/rental tools, not representative of full Pagila customer
  coverage.
- **No authentication layer.** `auth_required`/`auth_requirement` in
  `ToolSpec` document intent but are not enforced by a real auth
  middleware; `customer_id` is currently passed directly in the API
  request body.
- **Guardrail adds latency and cost.** Every specialist response triggers
  a second LLM call for review; acceptable for a support assistant, but a
  cheaper heuristic/regex pre-filter could reduce this in production.
- **No automated test runner wired into CI.** `app/evals/` is currently
  documentation plus a manually-invoked script, not enforced on every
  commit.
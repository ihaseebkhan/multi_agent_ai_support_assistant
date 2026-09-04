# Implementation Plan: Pagila Customer Support Assistant

## 1. Assumptions

- PostgreSQL is available locally with the Pagila sample dataset loaded via
  `database/pagila-schema.sql` / `database/pagila-data.sql`, and `DATABASE_URL`
  in `.env` points to it.
- A single demo customer (`customer_id=1`) is sufficient to validate
  subscription and rental-history flows.
- The OpenAI Agents SDK's native `handoffs` and `output_guardrails` are the
  required mechanisms for routing and safety, rather than custom manual
  dispatch logic.
- An in-process adapter satisfies "MCP-ready" for this phase; a real network
  MCP transport is a follow-up, not a blocker.
- Code is organized by responsibility (`app/tools/`, `app/agents/`,
  `app/guardrails/`, `app/mcp/`) rather than one monolithic module, to keep
  SQL, prompts, safety policy, and the MCP boundary independently reviewable.

## 2. Phases

### Phase 1 — Database and migrations
- Confirm Pagila schema/data load successfully.
- Add Alembic baseline (`a0ad47384753`) against the existing Pagila schema.
- Add `film.streaming_available` column (`e4432b255bb1`).
- Add `streaming_subscription` table with a seed row for `customer_id=1`
  (`96fadc45df62`).

### Phase 2 — Core tools and agents
- Implement `SupportContext`, `ToolExecutionError`, and shared response
  models in `app/models.py`.
- Implement one tool per module under `app/tools/`: `search_film_catalog`
  (`catalog.py`), `get_customer_streaming_subscription` (`subscription.py`),
  `get_customer_rental_history` (`rentals.py`), `search_kb`
  (`knowledge_base.py`, covering refunds, payment-method updates, and a
  general fallback), `create_handoff_ticket` (`escalation.py`), and
  `record_triage` (`triage.py`) — each backed by parameterized SQL where
  applicable, with structured success/error logging via `log_tool_call`
  (`app/tools/logging.py`).
- Implement one `Agent` per module under `app/agents/`
  (`catalog_agent.py`, `subscription_agent.py`, `rental_history_agent.py`,
  `knowledge_agent.py`, `human_handoff_agent.py`, `triage_agent.py`) using
  SDK `handoffs=[...]`, plus `hooks.py` for `SupportRunHooks`.
- Constrain `record_triage`'s `intent` argument to a fixed `Literal[...]`:
  `catalog_search`, `subscription_question`, `rental_history`,
  `knowledge_question`, `human_handoff`.

### Phase 3 — Safety and observability
- Add `support_output_guardrail` (`app/guardrails/output_guardrail.py`,
  `GuardrailReview` sub-agent) to every specialist agent.
- Add `SupportRunHooks.on_tool_start` (`app/agents/hooks.py`) to populate
  `used_tools`/`citations` on `SupportContext` dynamically (replacing any
  static placeholder values).

### Phase 4 — API layer
- Implement `POST /agent/respond` in `app/main.py`:
  request -> `handle_customer_request` -> `FinalAnswer` -> `AgentResponse`.
- Convert `OutputGuardrailTripwireTriggered` into a safe withheld response
  instead of a 500.
- Convert `ToolExecutionError` into an explicit `HTTPException(500)` rather
  than an unhandled stack trace.

### Phase 5 — MCP exposure
- Define `MCP_TOOL_METADATA` (`app/mcp/metadata.py`, a `ToolSpec` list)
  describing each tool's public contract, explicitly excluding trusted
  context fields (`customer_id`, `conversation_id`) from input schemas.
- Implement `LocalPagilaSupportMCPServer` (`app/mcp/server.py`,
  `pagila-support-mcp`) with `list_tools()` and an async `call_tool(...)`
  that constructs a `ToolContext` (not a plain `RunContextWrapper`) and
  invokes `FunctionTool.on_invoke_tool(...)`.
- Add `app/mcp/run_server.py` as a runnable smoke-test entry point
  (`python -m app.mcp.run_server`).

### Phase 6 — Evaluation
- Document 10 structured eval cases in `app/evals/evals.md`: prompt,
  expected intent/agent/tool, must-include/must-not-include terms, and
  safety behavior — covering all five agents plus a prompt-injection case
  and a nonexistent-customer resilience case.

## 3. Checklist

- [x] Alembic baseline + two follow-up migrations applied cleanly.
- [x] At least two tools backed by real SQL against Pagila
      (`search_film_catalog`, `get_customer_streaming_subscription`,
      `get_customer_rental_history`).
- [x] Routing implemented via SDK `handoffs`, not manual dispatch.
- [x] Trusted `SupportContext` propagated through every tool call.
- [x] Output guardrail wired to every specialist agent.
- [x] Guardrail trip converted to a safe API response, not a 500.
- [x] Dynamic `tools_used`/`citations`/`intent`/`confidence` in the API
      response.
- [x] `pagila-support-mcp` adapter exposing at least two database-backed
      tools with MCP-shaped metadata.
- [x] Codebase split by responsibility (`tools/`, `agents/`, `guardrails/`,
      `mcp/`) instead of one monolithic file.
- [x] 10-case eval suite documented (`app/evals/evals.md`) covering routing,
      content requirements, prompt injection, and graceful degradation.
- [ ] Executable eval runner wired to the documented cases (currently
      documentation only — no automated pass/fail script committed).
- [ ] Automated pytest tests for `list_tools()` / `call_tool()` and the
      ownership boundary (arguments cannot override trusted `customer_id`).
- [ ] Automated pytest tests for `/agent/respond` (happy path, guardrail-trip
      path, tool-failure path).
- [ ] Real MCP transport (`MCPServerStdio` or `MCPServerStreamableHttp`)
      wrapping the existing adapter.
- [ ] Auth middleware enforcing `auth_required` tools instead of trusting
      the request body's `customer_id`.
- [ ] `.gitignore` committed excluding `.env` before any push (secrets
      currently only protected locally).

## 4. Testing approach

- **Manual smoke test:** `python -m app.mcp.run_server` runs `list_tools()`
  and calls two database-backed tools end-to-end against a live Pagila
  database, printing real rows and structured tool-call logs.
- **API smoke test:** run the FastAPI app and `POST /agent/respond` with a
  known `customer_id`/message combination for each intent
  (`catalog_search`, `subscription_question`, `rental_history`,
  `knowledge_question`, `human_handoff`) and confirm `selected_agent`,
  `tools_used`, and `citations` match expectations.
- **Documented eval cases:** `app/evals/evals.md` — 10 prompts with expected
  intent/agent/tool, required/forbidden terms, and safety behavior,
  including a prompt-injection case (must not leak the system prompt) and a
  nonexistent-customer case (must fail gracefully, not crash or leak another
  customer's data).
- **Planned automated tests** (pytest + pytest-asyncio, not yet committed):
  - Execute each case in `app/evals/evals.md` programmatically and assert
    the documented expectations, rather than relying on manual inspection.
  - `pagila_support_server.list_tools()` includes the expected tool names
    and schemas.
  - `call_tool()` on each database-backed tool returns real rows for a
    known seeded customer/query.
  - `call_tool()` raises `ToolExecutionError` for an unknown tool name,
    malformed arguments, and a nonexistent customer.
  - A caller-supplied `customer_id` inside `arguments` cannot override the
    trusted `customer_id` keyword argument (ownership-boundary regression
    test).
  - `/agent/respond` returns `next_action="response_withheld"` (not a 500)
    when the guardrail trips.

## 5. Known limitations

See "Tradeoffs and known limitations" in `app/docs/design.md` — in-process
MCP adapter (not a network transport), mock KB/ticketing, single seeded demo
customer, no enforced auth layer, added guardrail latency/cost, and no
automated test runner wired into CI (evals currently documentation-only).
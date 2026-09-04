# AI Usage

## Tools used

GitHub Copilot Chat (agent mode), using Claude Sonnet 5, was used throughout
this project for:

- Drafting the Alembic migration chain (baseline import,
  `film.streaming_available` column, `streaming_subscription` table + seed
  data).
- Drafting the SQLAlchemy-backed tool implementations
  (`search_film_catalog`, `get_customer_streaming_subscription`,
  `get_customer_rental_history`, now in `app/tools/catalog.py`,
  `subscription.py`, `rentals.py`) and their structured logging via
  `log_tool_call` (`app/tools/logging.py`).
- Converting an initial manual if/else routing design into SDK-native
  `handoffs` across `TriageAgent` and the five specialist agents (now split
  one-per-file under `app/agents/`).
- Adding `SupportContext` propagation, `SupportRunHooks` for dynamic
  `tools_used`/`citations` tracking (`app/agents/hooks.py`), and the
  `support_output_guardrail` safety check (`app/guardrails/output_guardrail.py`).
- Extending `search_kb` (`app/tools/knowledge_base.py`) to cover
  payment-method update questions in addition to refunds and the general
  fallback, and updating `TriageAgent`'s instructions and `record_triage`'s
  `Literal` intent values to route those questions to `KnowledgeAgent`.
- Diagnosing and fixing a runtime `AttributeError` in the MCP adapter caused
  by passing a plain `RunContextWrapper` to `FunctionTool.on_invoke_tool`,
  which requires a `ToolContext` (found by reading the installed `agents`
  SDK source directly).
- Drafting the `MCP_TOOL_METADATA` / `ToolSpec` metadata
  (`app/mcp/metadata.py`) and the `LocalPagilaSupportMCPServer`
  (`pagila-support-mcp`, `app/mcp/server.py` + `app/mcp/run_server.py`).
- Proposing and carrying out the file-layout refactor from a single
  `app/agents/base.py` into responsibility-scoped modules
  (`app/models.py`, `app/tools/`, `app/guardrails/`, `app/agents/`,
  `app/mcp/`).
- Drafting the 10-case eval suite (`app/evals/evals.md`) covering routing,
  content requirements, prompt injection, and graceful degradation for a
  nonexistent customer.
- Drafting this documentation set (`docs/design.md`,
  `docs/implementation_plan.md`, `docs/ai_usage.md`).

## What was manually reviewed or changed

- All AI-suggested SQL was checked against the actual Pagila schema
  (`database/pagila-schema.sql`) before being accepted, to confirm table
  and column names (e.g. `film_category`, `inventory`, `streaming_subscription`).
- The `.env` file and `DATABASE_URL`, `OPENAI_API_KEY` configurations were set up and verified
  manually against a locally running PostgreSQL instance.
- Every AI code suggestion was run against the live database
  (`python -m app.mcp.run_server`, and the FastAPI endpoint) to confirm it
  worked end-to-end, not just that it looked correct.
- Tool ownership boundaries (customer_id/conversation_id sourced only from
  trusted `SupportContext`, never from model/tool arguments) were reviewed
  specifically for security implications before accepting the MCP adapter
  design.
- After the multi-file refactor, imports and module paths were verified by
  re-running the FastAPI app and the MCP smoke test, since splitting one
  file into many is mechanical but error-prone for import paths.
- The `.gitignore` recommendation was reviewed and deliberately kept
  minimal (`.env`, `__pycache__/`, `.venv/`) rather than accepting a larger
  generic template, since the actual risk in this repo is the committed
  `.env` secret, not incidental build artifacts.
- Decisions about scope (e.g., mock KB/ticketing instead of real tables, an
  in-process adapter instead of a full MCP network transport, documentation-
  only evals instead of a wired-in pytest suite) were made by the author to
  keep the implementation focused on the assignment's requirements.
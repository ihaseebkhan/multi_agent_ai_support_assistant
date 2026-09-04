from __future__ import annotations

import time

from agents import RunContextWrapper, function_tool

from app.models import HandoffTicket, SupportContext, ToolExecutionError
from app.tools.logging import log_tool_call


@function_tool
def create_handoff_ticket(
    ctx: RunContextWrapper[SupportContext],
    summary: str,
    reason: str,
) -> HandoffTicket:
    """Create a mock handoff ticket for an escalation or risky request."""
    conversation_id = ctx.context.conversation_id
    start = time.perf_counter()

    try:
        ticket = HandoffTicket(
            ticket_id="TCK-1001",
            summary=summary,
            reason=reason,
            status="open",
        )
        log_tool_call(
            conversation_id=conversation_id,
            tool_name="create_handoff_ticket",
            status="success",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return ticket
    except Exception as exc:
        log_tool_call(
            conversation_id=conversation_id,
            tool_name="create_handoff_ticket",
            status="error",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            error=str(exc),
        )
        raise ToolExecutionError(f"create_handoff_ticket failed: {exc}") from exc
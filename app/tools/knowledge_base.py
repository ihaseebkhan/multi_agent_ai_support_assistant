from __future__ import annotations

import time

from agents import RunContextWrapper, function_tool

from app.models import KBArticle, SupportContext, ToolExecutionError
from app.tools.logging import log_tool_call


@function_tool
def search_kb(
    ctx: RunContextWrapper[SupportContext],
    query: str,
) -> list[KBArticle]:
    """Search the local/mock KB and return support articles with source references."""
    conversation_id = ctx.context.conversation_id
    start = time.perf_counter()

    try:
        if "refund" in query.lower():
            articles = [
                KBArticle(
                    title="Refund policy",
                    answer="Refunds are handled by support after account verification.",
                    source="kb/refunds.md",
                )
            ]
        elif "payment method" in query.lower() or "payment" in query.lower():
            articles = [
                KBArticle(
                    title="Updating your payment method",
                    answer=(
                        "Go to Account Settings > Billing > Payment Methods, select "
                        "'Add or update payment method', and follow the prompts. "
                        "Changes apply to your next billing cycle."
                    ),
                    source="kb/payment_methods.md",
                )
            ]
        else:
            articles = [
                KBArticle(
                    title="General support",
                    answer="The knowledge base does not contain a confident answer for this question.",
                    source="kb/general.md",
                )
            ]

        log_tool_call(
            conversation_id=conversation_id,
            tool_name="search_kb",
            status="success",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return articles
    except Exception as exc:
        log_tool_call(
            conversation_id=conversation_id,
            tool_name="search_kb",
            status="error",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            error=str(exc),
        )
        raise ToolExecutionError(f"search_kb failed: {exc}") from exc
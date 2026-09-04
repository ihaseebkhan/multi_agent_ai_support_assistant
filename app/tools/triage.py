from __future__ import annotations

from typing import Literal

from agents import RunContextWrapper, function_tool

from app.models import SupportContext


@function_tool
def record_triage(
    ctx: RunContextWrapper[SupportContext],
    intent: Literal[
        "catalog_search",
        "subscription_question",
        "rental_history",
        "knowledge_question",
        "human_handoff",
    ],
    confidence: float,
) -> str:
    """Record the request classification and confidence before handing off."""

    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")

    ctx.context.intent = intent
    ctx.context.confidence = confidence
    return "Triage decision recorded."
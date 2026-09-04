from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

MODEL_CHOICE = os.getenv("MODEL_CHOICE", "gpt-4o-mini")


@dataclass
class SupportContext:
    customer_id: int
    conversation_id: str
    used_tools: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    intent: str = "unknown"
    confidence: float = 0.0


class ToolExecutionError(RuntimeError):
    """Raised when a tool fails validation or execution."""


class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    error_behavior: str
    auth_required: bool = False
    auth_requirement: str | None = None
    ownership_boundary: str = (
        "customer-scoped; only the explicit customer_id or current scoped customer may be used."
    )
    function: Any


class FinalAnswer(BaseModel):
    answer: str
    selected_agent: str
    tools_used: list[str]
    citations: list[str]
    intent: str
    confidence: float


class FilmCatalogMatch(BaseModel):
    title: str
    category: str
    rating: str
    rental_rate: float
    streaming_available: bool


class SubscriptionInfo(BaseModel):
    customer_id: int
    plan_name: str
    status: str
    renewal_date: str | None
    auto_renew: bool


class RentalHistoryItem(BaseModel):
    film_title: str
    rental_date: str
    return_date: str | None


class KBArticle(BaseModel):
    title: str
    answer: str
    source: str


class HandoffTicket(BaseModel):
    ticket_id: str
    summary: str
    reason: str
    status: str = "open"


class ToolCallLog(BaseModel):
    conversation_id: str
    tool_name: str
    status: Literal["success", "error"]
    latency_ms: float
    error: str | None = None


class GuardrailDecision(BaseModel):
    blocked: bool
    reason: str
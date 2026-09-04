from __future__ import annotations

from app.models import ToolSpec
from app.tools.catalog import search_film_catalog
from app.tools.escalation import create_handoff_ticket
from app.tools.knowledge_base import search_kb
from app.tools.rentals import get_customer_rental_history
from app.tools.subscription import get_customer_streaming_subscription
from app.tools.triage import record_triage

MCP_TOOL_METADATA: list[ToolSpec] = [
    ToolSpec(
        name="search_film_catalog",
        description="Search the Pagila catalog for film metadata including title, category, rating, rental rate, and streaming availability.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Film title or category search text.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "category": {"type": "string"},
                    "rating": {"type": "string"},
                    "rental_rate": {"type": "number"},
                    "streaming_available": {"type": "boolean"},
                },
            },
        },
        error_behavior=(
            "Raises ToolExecutionError after logging a failed database query. "
            "The caller receives a safe tool-failure message."
        ),
        auth_required=False,
        auth_requirement=None,
        ownership_boundary="catalog-scoped; returns no customer-specific data.",
        function=search_film_catalog,
    ),
    ToolSpec(
        name="get_customer_streaming_subscription",
        description="Read the customer's current streaming subscription status from the migrated subscription table.",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "plan_name": {"type": "string"},
                "status": {"type": "string"},
                "renewal_date": {"type": ["string", "null"]},
                "auto_renew": {"type": "boolean"},
            },
        },
        error_behavior="Return a structured tool error with status=error and the exception text; never expose raw database internals.",
        auth_required=True,
        auth_requirement=(
            "Authenticated customer session or authorized support-user access."
        ),
        ownership_boundary=(
            "customer-scoped; reads only the customer_id held in SupportContext "
            "and never accepts a model-provided customer ID."
        ),
        function=get_customer_streaming_subscription,
    ),
    ToolSpec(
        name="get_customer_rental_history",
        description="Join customer, rental, inventory, and film tables to return recent rentals for a customer.",
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "film_title": {"type": "string"},
                    "rental_date": {"type": "string"},
                    "return_date": {"type": ["string", "null"]},
                },
            },
        },
        error_behavior="Return a structured tool error with status=error and the exact failure reason.",
        auth_required=True,
        auth_requirement=(
            "Authenticated customer session or authorized support-user access."
        ),
        ownership_boundary=(
            "customer-scoped; reads only the customer_id held in SupportContext "
            "and never accepts a model-provided customer ID."
        ),
        function=get_customer_rental_history,
    ),
    ToolSpec(
        name="search_kb",
        description="Search the local/mock KB and include source references when a support article is found.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Support question or search keywords.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "answer": {"type": "string"},
                    "source": {"type": "string"},
                },
            },
        },
        error_behavior="Return a structured tool error with status=error and the exception text.",
        auth_required=False,
        ownership_boundary="knowledge-base scoped; no customer-specific data is returned.",
        function=search_kb,
    ),
    ToolSpec(
        name="create_handoff_ticket",
        description="Create a mock ticket for escalation or risky requests for human support.",
        input_schema={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Concise summary of the escalation.",
                },
                "reason": {
                    "type": "string",
                    "description": "Why human support is required.",
                },
            },
            "required": ["summary", "reason"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "summary": {"type": "string"},
                "reason": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        error_behavior="Return a structured tool error with status=error and the exception text; do not silently skip escalation.",
        auth_required=False,
        ownership_boundary="support-team scoped; only a ticket record is created and no account changes are made.",
        function=create_handoff_ticket,
    ),
    ToolSpec(
        name="record_triage",
        description=(
            "Internal triage tool that records the classified request intent and "
            "confidence before the TriageAgent hands off to a specialist."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [
                        "catalog",
                        "subscription",
                        "rental_history",
                        "knowledge",
                        "human_handoff",
                    ],
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": ["intent", "confidence"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "string",
            "description": "Confirmation that the triage details were recorded.",
        },
        error_behavior=(
            "Raises ValueError when confidence is outside 0 to 1. "
            "No customer database data is accessed."
        ),
        auth_required=False,
        auth_requirement=None,
        ownership_boundary=(
            "internal routing only; writes intent and confidence to SupportContext."
        ),
        function=record_triage,
    ),
]
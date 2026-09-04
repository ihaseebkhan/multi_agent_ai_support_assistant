from __future__ import annotations

from agents import Agent

from app.guardrails.output_guardrail import support_output_guardrail
from app.models import MODEL_CHOICE, HandoffTicket
from app.tools.escalation import create_handoff_ticket

human_handoff_agent = Agent(
    name="HumanHandoffAgent",
    handoff_description="Handles escalations, sensitive requests, account-risk issues, and requests that require a human support representative.",
    model=MODEL_CHOICE,
    tools=[create_handoff_ticket],
    output_guardrails=[support_output_guardrail],
    output_type=HandoffTicket,
    instructions=(
        "Handle escalation and risky requests. "
        "You MUST call create_handoff_ticket exactly once before responding. "
        "Copy the ticket_id, summary, reason, and status from the tool result "
        "into your final structured output. "
        "Do not perform sensitive account changes directly."
    ),
)
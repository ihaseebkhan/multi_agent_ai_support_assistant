from __future__ import annotations

from agents import Agent

from app.guardrails.output_guardrail import support_output_guardrail
from app.models import MODEL_CHOICE
from app.tools.rentals import get_customer_rental_history

rental_history_agent = Agent(
    name="RentalHistoryAgent",
    handoff_description="Handles customer rental history and recent film rentals.",
    model=MODEL_CHOICE,
    tools=[get_customer_rental_history],
    output_guardrails=[support_output_guardrail],
    instructions=(
        "Answer recent rental questions. "
        "Use get_customer_rental_history and summarize recent rentals."
    ),
)
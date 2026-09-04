from __future__ import annotations

from agents import Agent

from app.guardrails.output_guardrail import support_output_guardrail
from app.models import MODEL_CHOICE
from app.tools.subscription import get_customer_streaming_subscription

subscription_agent = Agent(
    name="SubscriptionAgent",
    handoff_description="Handles customer streaming subscription plans, status, renewal dates, and auto-renew settings.",
    model=MODEL_CHOICE,
    tools=[get_customer_streaming_subscription],
    output_guardrails=[support_output_guardrail],
    instructions=(
        "Answer subscription and renewal questions. "
        "Use get_customer_streaming_subscription. "
        "Protect customer context and handle missing data carefully."
    ),
)
from __future__ import annotations

from agents import Agent

from app.agents.catalog_agent import catalog_agent
from app.agents.human_handoff_agent import human_handoff_agent
from app.agents.knowledge_agent import knowledge_agent
from app.agents.rental_history_agent import rental_history_agent
from app.agents.subscription_agent import subscription_agent
from app.models import MODEL_CHOICE
from app.tools.triage import record_triage

triage_agent = Agent(
    name="TriageAgent",
    model=MODEL_CHOICE,
    tools=[record_triage],
    instructions=(
        "Before handing off, you MUST call record_triage exactly once. "
        "Classify the customer's request and hand off to the best specialist agent. "
        "Choose CatalogAgent for film catalog, category, rating, rental price, "
        "or streaming availability questions. "
        "Choose SubscriptionAgent for streaming subscription plan, status, "
        "renewal date, or auto-renew questions. "
        "Choose RentalHistoryAgent for a customer's recent or previous rentals. "
        "Choose KnowledgeAgent for general support, policies, FAQ-style questions, "
        "and account/billing questions such as updating a payment method. "
        "Choose HumanHandoffAgent for subscription cancellation requests. "
        "Choose HumanHandoffAgent for sensitive requests, risky account actions, "
        "complaints, or requests that cannot be answered confidently. "
        "Use exactly one handoff. Do not answer the customer directly. "
        "When the request is ambiguous or confidence is low, hand off to HumanHandoffAgent."
    ),
    handoffs=[
        catalog_agent,
        subscription_agent,
        rental_history_agent,
        knowledge_agent,
        human_handoff_agent,
    ],
)
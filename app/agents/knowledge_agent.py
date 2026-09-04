from __future__ import annotations

from agents import Agent

from app.guardrails.output_guardrail import support_output_guardrail
from app.models import MODEL_CHOICE
from app.tools.knowledge_base import search_kb

knowledge_agent = Agent(
    name="KnowledgeAgent",
    handoff_description="Handles general support questions, policies, and knowledge-base information.",
    model=MODEL_CHOICE,
    tools=[search_kb],
    output_guardrails=[support_output_guardrail],
    instructions=(
        "Answer general support questions using search_kb. "
        "Include source references when available. "
        "If the KB does not contain the answer, say so clearly."
    ),
)
from __future__ import annotations

from agents import Agent

from app.guardrails.output_guardrail import support_output_guardrail
from app.models import MODEL_CHOICE
from app.tools.catalog import search_film_catalog

catalog_agent = Agent(
    name="CatalogAgent",
    handoff_description=(
        "Handles film catalog, movie metadata, categories, ratings, rental "
        "prices, and streaming availability."
    ),
    model=MODEL_CHOICE,
    tools=[search_film_catalog],
    output_guardrails=[support_output_guardrail],
    instructions=(
        "Answer film and streaming questions. "
        "Use search_film_catalog. "
        "Mention title, category, rating, rental rate, and streaming availability."
    ),
)
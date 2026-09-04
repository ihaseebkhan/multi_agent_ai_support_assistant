from __future__ import annotations

from agents import Agent, RunContextWrapper, RunHooks, Tool

from app.models import SupportContext


class SupportRunHooks(RunHooks[SupportContext]):
    TOOL_CITATIONS = {
        "search_film_catalog": "Pagila film catalog",
        "get_customer_streaming_subscription": "Pagila streaming_subscription table",
        "get_customer_rental_history": "Pagila rental history",
        "search_kb": "Support knowledge base",
        "create_handoff_ticket": "Support handoff ticket system",
    }

    async def on_tool_start(
        self,
        context: RunContextWrapper[SupportContext],
        agent: Agent,
        tool: Tool,
    ) -> None:
        tool_name = tool.name

        if tool_name not in context.context.used_tools:
            context.context.used_tools.append(tool_name)

        citation = self.TOOL_CITATIONS.get(tool_name)
        if citation and citation not in context.context.citations:
            context.context.citations.append(citation)
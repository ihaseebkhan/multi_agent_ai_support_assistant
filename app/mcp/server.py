from __future__ import annotations

import json
import uuid
from typing import Any

from agents.tool_context import ToolContext

from app.mcp.metadata import MCP_TOOL_METADATA
from app.models import SupportContext, ToolExecutionError, ToolSpec


class LocalPagilaSupportMCPServer:
    """MCP-shaped local adapter for Pagila support tools; replaceable by a real MCP transport."""

    server_name = "pagila-support-mcp"

    def __init__(self, tools: list[ToolSpec] | None = None):
        self.tools = {tool.name: tool for tool in (tools or MCP_TOOL_METADATA)}

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "outputSchema": tool.output_schema,
                "errorBehavior": tool.error_behavior,
                "authRequired": tool.auth_required,
                "authRequirement": tool.auth_requirement,
                "ownershipBoundary": tool.ownership_boundary,
            }
            for tool in self.tools.values()
        ]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        customer_id: int,
        conversation_id: str,
    ) -> Any:
        tool = self.tools.get(name)
        if tool is None:
            raise ToolExecutionError(f"Unknown tool: {name}")

        context = SupportContext(customer_id=customer_id, conversation_id=conversation_id)
        arguments_json = json.dumps(arguments)
        tool_context = ToolContext(
            context=context,
            tool_name=name,
            tool_call_id=str(uuid.uuid4()),  # SDK requires an id even outside a real model turn
            tool_arguments=arguments_json,
        )

        try:
            return await tool.function.on_invoke_tool(tool_context, arguments_json)
        except TypeError as exc:
            raise ToolExecutionError(f"Invalid arguments for {name}: {exc}") from exc
        except Exception as exc:
            raise ToolExecutionError(f"Tool {name} failed: {exc}") from exc


pagila_support_server = LocalPagilaSupportMCPServer()
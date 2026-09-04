from __future__ import annotations

import asyncio

from app.mcp.server import pagila_support_server


async def main() -> None:
    print(f"Server: {pagila_support_server.server_name}")
    for tool in pagila_support_server.list_tools():
        print(tool["name"], "-", tool["description"])

    # verify at least two database-backed tools are reachable through the adapter
    catalog = await pagila_support_server.call_tool(
        "search_film_catalog", {"query": "academy"}, customer_id=1, conversation_id="mcp-check"
    )
    print("search_film_catalog ->", catalog)

    subscription = await pagila_support_server.call_tool(
        "get_customer_streaming_subscription", {}, customer_id=1, conversation_id="mcp-check"
    )
    print("get_customer_streaming_subscription ->", subscription)


if __name__ == "__main__":
    asyncio.run(main())
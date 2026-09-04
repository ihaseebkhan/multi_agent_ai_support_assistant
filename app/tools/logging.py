from __future__ import annotations

import json

from app.models import ToolCallLog


def log_tool_call(
    *,
    conversation_id: str,
    tool_name: str,
    status: str,
    latency_ms: float,
    error: str | None = None,
) -> None:
    payload = ToolCallLog(
        conversation_id=conversation_id,
        tool_name=tool_name,
        status=status,
        latency_ms=latency_ms,
        error=error,
    )
    print(json.dumps(payload.model_dump(), default=str))
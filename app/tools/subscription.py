from __future__ import annotations

import time

from agents import RunContextWrapper, function_tool
from sqlalchemy import text

from app.database import engine
from app.models import SubscriptionInfo, SupportContext, ToolExecutionError
from app.tools.logging import log_tool_call


@function_tool
def get_customer_streaming_subscription(
    ctx: RunContextWrapper[SupportContext],
) -> SubscriptionInfo:
    customer_id = ctx.context.customer_id
    conversation_id = ctx.context.conversation_id
    start = time.perf_counter()

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT
                        customer_id,
                        plan_name,
                        status,
                        end_date AS renewal_date,
                        auto_renew
                    FROM streaming_subscription
                    WHERE customer_id = :customer_id
                    ORDER BY start_date DESC
                    LIMIT 1
                """),
                {"customer_id": customer_id},
            ).mappings().first()

        if row is None:
            raise ValueError("No streaming subscription found for this customer.")

        info = SubscriptionInfo(
            customer_id=int(row["customer_id"]),
            plan_name=row["plan_name"],
            status=row["status"],
            renewal_date=(
                row["renewal_date"].isoformat()
                if row["renewal_date"]
                else None
            ),
            auto_renew=bool(row["auto_renew"]),
        )

        log_tool_call(
            conversation_id=conversation_id,
            tool_name="get_customer_streaming_subscription",
            status="success",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return info
    except Exception as exc:
        log_tool_call(
            conversation_id=conversation_id,
            tool_name="get_customer_streaming_subscription",
            status="error",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            error=str(exc),
        )
        raise ToolExecutionError(
            f"get_customer_streaming_subscription failed: {exc}"
        ) from exc
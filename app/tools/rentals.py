from __future__ import annotations

import time

from agents import RunContextWrapper, function_tool
from sqlalchemy import text

from app.database import engine
from app.models import RentalHistoryItem, SupportContext, ToolExecutionError
from app.tools.logging import log_tool_call


@function_tool
def get_customer_rental_history(
    ctx: RunContextWrapper[SupportContext],
) -> list[RentalHistoryItem]:
    customer_id = ctx.context.customer_id
    conversation_id = ctx.context.conversation_id
    start = time.perf_counter()

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        f.title AS film_title,
                        r.rental_date,
                        r.return_date
                    FROM rental r
                    JOIN inventory i ON i.inventory_id = r.inventory_id
                    JOIN film f ON f.film_id = i.film_id
                    WHERE r.customer_id = :customer_id
                    ORDER BY r.rental_date DESC
                    LIMIT 10
                """),
                {"customer_id": customer_id},
            )

            rows = [
                RentalHistoryItem(
                    film_title=row["film_title"],
                    rental_date=row["rental_date"].isoformat(),
                    return_date=(
                        row["return_date"].isoformat()
                        if row["return_date"]
                        else None
                    ),
                )
                for row in result.mappings().all()
            ]

        log_tool_call(
            conversation_id=conversation_id,
            tool_name="get_customer_rental_history",
            status="success",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return rows
    except Exception as exc:
        log_tool_call(
            conversation_id=conversation_id,
            tool_name="get_customer_rental_history",
            status="error",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            error=str(exc),
        )
        raise ToolExecutionError(
            f"get_customer_rental_history failed: {exc}"
        ) from exc
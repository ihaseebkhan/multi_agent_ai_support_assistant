from __future__ import annotations

import time

from agents import RunContextWrapper, function_tool
from sqlalchemy import text

from app.database import engine
from app.models import FilmCatalogMatch, SupportContext, ToolExecutionError
from app.tools.logging import log_tool_call


@function_tool
def search_film_catalog(
    ctx: RunContextWrapper[SupportContext],
    query: str,
) -> list[FilmCatalogMatch]:
    """Search the Pagila film catalog for movie metadata, including title, category, rating, rental rate, and streaming availability."""
    conversation_id = ctx.context.conversation_id
    start = time.perf_counter()
    try:
        term = f"%{query.lower()}%"
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        f.title,
                        c.name AS category,
                        f.rating,
                        f.rental_rate,
                        COALESCE(f.streaming_available, false) AS streaming_available
                    FROM film f
                    LEFT JOIN film_category fc ON fc.film_id = f.film_id
                    LEFT JOIN category c ON c.category_id = fc.category_id
                    WHERE LOWER(f.title) LIKE :term
                       OR LOWER(c.name) LIKE :term
                    ORDER BY f.title
                    LIMIT 10
                """),
                {"term": term},
            )

            rows = [
                FilmCatalogMatch(
                    title=row["title"],
                    category=row["category"] or "Uncategorized",
                    rating=str(row["rating"]),
                    rental_rate=float(row["rental_rate"]),
                    streaming_available=bool(row["streaming_available"]),
                )
                for row in result.mappings().all()
            ]

        log_tool_call(
            conversation_id=conversation_id,
            tool_name="search_film_catalog",
            status="success",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return rows
    except Exception as exc:
        log_tool_call(
            conversation_id=conversation_id,
            tool_name="search_film_catalog",
            status="error",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            error=str(exc),
        )
        raise ToolExecutionError(f"search_film_catalog failed: {exc}") from exc
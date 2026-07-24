"""Persistence layer for analysis records using asyncpg."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import asyncpg
from app.config import settings


def _db_url() -> str:
    """Return a plain postgres URL suitable for asyncpg."""
    url = settings.database_url
    # Strip sqlalchemy driver prefix if present
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    return url


_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool:
    """Lazy-initialised connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(_db_url(), min_size=1, max_size=10)
    return _pool


async def create_analysis(
    analysis_id: str,
    user_id: str,
    request_dict: dict[str, Any],
) -> None:
    """Insert a new analysis row with status 'running'."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO analyses (id, user_id, request, status)
            VALUES ($1, $2, $3::jsonb, $4)
            """,
            analysis_id,
            user_id,
            json.dumps(request_dict),
            "running",
        )


async def update_analysis(
    analysis_id: str,
    result_dict: dict[str, Any] | None,
    status: str,
) -> None:
    """Update result, status and completed_at for an analysis."""
    pool = await _get_pool()
    completed_at = datetime.now(timezone.utc) if status == "done" else None
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE analyses
            SET result = $1::jsonb, status = $2, completed_at = $3
            WHERE id = $4
            """,
            json.dumps(result_dict) if result_dict is not None else None,
            status,
            completed_at,
            analysis_id,
        )


async def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    """Fetch a single analysis row by id."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, request, result, status, created_at, completed_at
            FROM analyses
            WHERE id = $1
            """,
            analysis_id,
        )
    if row is None:
        return None

    record = dict(row)
    # asyncpg returns jsonb columns as JSON strings; parse them back into dicts.
    if isinstance(record.get("request"), str):
        record["request"] = json.loads(record["request"])
    if isinstance(record.get("result"), str) and record["result"] is not None:
        record["result"] = json.loads(record["result"])
    return record

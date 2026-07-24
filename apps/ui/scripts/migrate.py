#!/usr/bin/env python3
"""Apply SQL migrations from docs/sql."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ui.config import settings

ROOT = Path(__file__).resolve().parents[3]
SQL_DIR = ROOT / "docs" / "sql"


def main() -> int:
    if not SQL_DIR.is_dir():
        print(f"SQL directory not found: {SQL_DIR}", file=sys.stderr)
        return 1

    files = sorted(SQL_DIR.glob("*.sql"))
    if not files:
        print(f"No .sql files in {SQL_DIR}", file=sys.stderr)
        return 1

    url = settings.sync_database_url()
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                # Strip drizzle-style breakpoints
                statements = [
                    s.strip()
                    for s in sql.replace("--> statement-breakpoint", ";").split(";")
                    if s.strip()
                ]
                print(f"Applying {path.name} ({len(statements)} statements)…")
                for stmt in statements:
                    cur.execute(stmt)
        conn.commit()

    print("Migrations applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

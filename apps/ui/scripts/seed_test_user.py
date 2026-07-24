#!/usr/bin/env python3
"""Seed the standard local test user."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ui.auth.users import create_user, get_user_by_email

EMAIL = "mundo.dev@cv-analyzer.local"
PASSWORD = "f3l!pe_p@llm@"


def main() -> int:
    existing = get_user_by_email(EMAIL)
    if existing is not None:
        print(f"Test user already exists: {existing.id}")
        return 0
    try:
        user_id = create_user(EMAIL, PASSWORD, is_admin=True)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to seed test user: {exc}", file=sys.stderr)
        return 1
    print(f"Created test user {user_id}")
    print(f"  email: {EMAIL}")
    print(f"  password: {PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create an invite-only user in Postgres."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ui.auth.users import create_user


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a user for DevRoadmap")
    parser.add_argument("email", nargs="?", help="User email")
    parser.add_argument("password", nargs="?", help="User password")
    parser.add_argument("--admin", action="store_true", help="Mark user as admin")
    args = parser.parse_args()

    email = args.email or input("Email: ").strip()
    password = args.password or getpass.getpass("Password: ")
    if not email or not password:
        print("Email and password are required.", file=sys.stderr)
        return 1

    try:
        user_id = create_user(email, password, is_admin=args.admin)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to create user: {exc}", file=sys.stderr)
        return 1

    print(f"Created user {user_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

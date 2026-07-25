"""Seed Qdrant roadmap_nodes from docs/archives.

Usage (from apps/api):
  uv run python scripts/seed_qdrant.py
  uv run python scripts/seed_qdrant.py --force
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow `python scripts/seed_qdrant.py` without install layout issues
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag.seeder import seed_roadmap_collection  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Qdrant roadmap_nodes collection")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop and recreate the collection before seeding",
    )
    args = parser.parse_args()
    n = asyncio.run(seed_roadmap_collection(force=args.force))
    print(f"done upserted={n}", flush=True)
    raise SystemExit(0 if n >= 0 else 1)


if __name__ == "__main__":
    main()

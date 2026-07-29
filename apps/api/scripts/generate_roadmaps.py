"""Generate nested roadmap JSON from markdown archives (with hash check).

Usage (from apps/api):
  uv run python scripts/generate_roadmaps.py
  uv run python scripts/generate_roadmaps.py --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from roadmap.archive_parser import ArchiveParser, generate_nested_structure  # noqa: E402
from roadmap.manifest import (  # noqa: E402
    calculate_source_hash,
    save_manifest,
    should_regenerate,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate roadmap JSON files")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if hashes match",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    archives_dir = repo_root / "docs" / "archives"
    data_dir = repo_root / "data" / "roadmaps"

    if not archives_dir.is_dir():
        print(f"ERROR: Archives directory not found: {archives_dir}", file=sys.stderr)
        return 1

    md_files = sorted(archives_dir.glob("roadmap-*.md"))
    if not md_files:
        print(f"ERROR: No roadmap-*.md files in {archives_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(md_files)} roadmap archive(s)")

    if not args.force:
        should_regen, reason = should_regenerate(archives_dir, data_dir)
        if not should_regen:
            print(f"Roadmap data up to date ({reason})")
            return 0
        print(f"Regenerating roadmap data: {reason}")
    else:
        print("Force regeneration requested")

    data_dir.mkdir(parents=True, exist_ok=True)

    parser_instance = ArchiveParser()
    total_stats = {"roadmaps": 0, "groups": 0, "skills": 0}
    source_hashes = calculate_source_hash(archives_dir)

    for md_file in md_files:
        print(f"  Processing: {md_file.name}")
        try:
            metadata, levels = parser_instance.parse_file(md_file)
            generate_nested_structure(metadata, levels, data_dir)
            total_stats["roadmaps"] += 1
            total_stats["groups"] += len(levels[0].groups) if levels else 0
            for lvl in levels:
                total_stats["groups"] += len(lvl.groups)
                for grp in lvl.groups:
                    total_stats["skills"] += len(grp.skills)
        except Exception as exc:
            print(f"  ERROR processing {md_file.name}: {exc}", file=sys.stderr)
            return 1

    save_manifest(data_dir, source_hashes, total_stats)

    print(
        f"Generated {total_stats['roadmaps']} roadmap(s), "
        f"{total_stats['groups']} groups, {total_stats['skills']} skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Hash-based change detection for roadmap archive regeneration."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate_source_hash(archives_dir: Path) -> dict:
    """Calculate hashes of all markdown archive files.

    Returns a dict mapping filename to sha256 hash.
    """
    result: dict = {}
    for md_file in sorted(archives_dir.glob("roadmap-*.md")):
        result[md_file.name] = _file_hash(md_file)
    return result


def calculate_combined_hash(file_hashes: dict) -> str:
    """Create a single combined hash from all individual file hashes.

    The combined hash is deterministic regardless of dict iteration order.
    """
    h = hashlib.sha256()
    for filename in sorted(file_hashes):
        h.update(f"{filename}:{file_hashes[filename]}".encode("utf-8"))
    return h.hexdigest()


def load_manifest(data_dir: Path) -> dict | None:
    """Load existing manifest from data directory.

    Returns None if manifest is missing or invalid.
    """
    manifest_path = data_dir / ".manifest.json"
    if not manifest_path.is_file():
        return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        required_keys = {"version", "source_hash", "source_files"}
        if not required_keys.issubset(manifest.keys()):
            return None

        return manifest
    except (json.JSONDecodeError, OSError, KeyError):
        return None


def save_manifest(
    data_dir: Path,
    source_hashes: dict,
    stats: dict,
) -> None:
    """Write manifest with timestamp, hashes and generation stats."""
    combined = calculate_combined_hash(source_hashes)

    manifest = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_hash": combined,
        "source_files": source_hashes,
        "output_summary": {
            "roadmaps": stats.get("roadmaps", 0),
            "groups": stats.get("groups", 0),
            "skills": stats.get("skills", 0),
        },
    }

    manifest_path = data_dir / ".manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def should_regenerate(archives_dir: Path, data_dir: Path) -> tuple[bool, str]:
    """Check if roadmap data regeneration is needed.

    Returns (should_regenerate: bool, reason: str).

    Reasons:
        - "no_manifest": No manifest file exists
        - "no_source_files": No markdown archives found
        - "hash_mismatch": One or more archive files changed
        - "file_added": New archive file detected
        - "file_removed": Archive file was removed
        - "up_to_date": Everything matches, no regeneration needed
    """
    source_hashes = calculate_source_hash(archives_dir)

    if not source_hashes:
        return True, "no_source_files"

    manifest = load_manifest(data_dir)
    if manifest is None:
        return True, "no_manifest"

    stored_files = set(manifest.get("source_files", {}).keys())
    current_files = set(source_hashes.keys())

    # Check for added or removed files
    added = current_files - stored_files
    removed = stored_files - current_files

    if added or removed:
        reasons = []
        if added:
            reasons.append(f"added: {', '.join(sorted(added))}")
        if removed:
            reasons.append(f"removed: {', '.join(sorted(removed))}")
        return True, "; ".join(reasons)

    # Check hash mismatches
    mismatches = []
    for filename, current_hash in source_hashes.items():
        stored_hash = manifest["source_files"].get(filename)
        if stored_hash != current_hash:
            mismatches.append(filename)

    if mismatches:
        return True, f"hash_mismatch ({', '.join(mismatches)} changed)"

    return False, "up_to_date"
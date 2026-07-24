# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Cross-platform project orchestration (Windows / macOS / Linux).

Usage (from repo root):
  uv run scripts/run.py setup
  uv run scripts/run.py api
  uv run scripts/run.py ui
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "apps" / "api"
UI = ROOT / "apps" / "ui"


def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> int:
    print(f"+ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=cwd or ROOT, check=False)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode


def _uv(*args: str, cwd: Path, check: bool = True) -> int:
    return _run(["uv", *args], cwd=cwd, check=check)


def cmd_env(_: argparse.Namespace) -> None:
    dest = ROOT / ".env"
    src = ROOT / ".env.example"
    if dest.exists():
        print(f".env already exists at {dest}")
        return
    if not src.is_file():
        print(f"Missing {src}", file=sys.stderr)
        raise SystemExit(1)
    shutil.copyfile(src, dest)
    print(f"Created {dest} from .env.example")


def cmd_install(_: argparse.Namespace) -> None:
    _uv("sync", cwd=API)
    _uv("sync", cwd=UI)


def cmd_infra_up(_: argparse.Namespace) -> None:
    _run(["docker", "compose", "up", "-d", "postgres", "qdrant"])


def cmd_infra_down(_: argparse.Namespace) -> None:
    _run(["docker", "compose", "down"])


def cmd_migrate(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/migrate.py", cwd=UI)


def cmd_seed_test(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/seed_test_user.py", cwd=UI)


def cmd_seed_admin(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/create_user.py", "--admin", cwd=UI)


def cmd_api(_: argparse.Namespace) -> None:
    _uv(
        "run",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--port",
        "8000",
        "--app-dir",
        "src",
        cwd=API,
    )


def cmd_ui(_: argparse.Namespace) -> None:
    _uv(
        "run",
        "streamlit",
        "run",
        "src/ui/app.py",
        "--server.port",
        "8501",
        cwd=UI,
    )


def cmd_test(_: argparse.Namespace) -> None:
    code = _uv("run", "pytest", cwd=API, check=False)
    code |= _uv("run", "pytest", cwd=UI, check=False)
    raise SystemExit(code)


def cmd_lint(_: argparse.Namespace) -> None:
    code = _uv("run", "ruff", "check", ".", cwd=API, check=False)
    code |= _uv("run", "ruff", "check", "src", "scripts", cwd=UI, check=False)
    raise SystemExit(code)


def cmd_setup(args: argparse.Namespace) -> None:
    cmd_env(args)
    cmd_install(args)
    cmd_infra_up(args)
    cmd_migrate(args)
    cmd_seed_test(args)
    print()
    print("Setup complete.")
    print("  Terminal 1: uv run scripts/run.py api")
    print("  Terminal 2: uv run scripts/run.py ui")
    print("  Open http://localhost:8501")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DevRoadmap orchestration (uv + docker).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    handlers = {
        "env": cmd_env,
        "install": cmd_install,
        "infra-up": cmd_infra_up,
        "infra-down": cmd_infra_down,
        "migrate": cmd_migrate,
        "seed-test": cmd_seed_test,
        "seed-admin": cmd_seed_admin,
        "api": cmd_api,
        "ui": cmd_ui,
        "test": cmd_test,
        "lint": cmd_lint,
        "setup": cmd_setup,
    }

    for name in handlers:
        sub.add_parser(name)

    args = parser.parse_args()
    handlers[args.command](args)


if __name__ == "__main__":
    main()

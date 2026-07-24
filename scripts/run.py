# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Cross-platform project orchestration (Windows / macOS / Linux).

Usage (from repo root):
  uv run scripts/run.py setup
  uv run scripts/run.py dev
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "apps" / "api"
UI = ROOT / "apps" / "ui"
ROOT_ENV = ROOT / ".env"


def _load_root_env(path: Path = ROOT_ENV) -> dict[str, str]:
    """Parse KEY=VALUE lines from .env (no external deps)."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def _merged_env() -> dict[str, str]:
    """OS env + root .env (root .env wins for keys it defines)."""
    env = dict(os.environ)
    env.update(_load_root_env())
    return env


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> int:
    print(f"+ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=cwd or ROOT, check=False, env=env)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode


def _uv(*args: str, cwd: Path, check: bool = True, env: dict[str, str] | None = None) -> int:
    return _run(["uv", *args], cwd=cwd, check=check, env=env)


def cmd_env(_: argparse.Namespace) -> None:
    dest = ROOT_ENV
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
    env = _merged_env()
    _uv("sync", cwd=API, env=env)
    _uv("sync", cwd=UI, env=env)


def cmd_infra_up(_: argparse.Namespace) -> None:
    _run(["docker", "compose", "up", "-d", "postgres", "qdrant"], env=_merged_env())


def cmd_infra_down(_: argparse.Namespace) -> None:
    _run(["docker", "compose", "down"], env=_merged_env())


def cmd_migrate(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/migrate.py", cwd=UI, env=_merged_env())


def cmd_seed_test(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/seed_test_user.py", cwd=UI, env=_merged_env())


def cmd_seed_admin(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/create_user.py", "--admin", cwd=UI, env=_merged_env())


def cmd_api(_: argparse.Namespace) -> None:
    _uv(
        "run",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--app-dir",
        "src",
        cwd=API,
        env=_merged_env(),
    )


def cmd_ui(_: argparse.Namespace) -> None:
    _uv(
        "run",
        "streamlit",
        "run",
        "src/ui/app.py",
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1",
        cwd=UI,
        env=_merged_env(),
    )


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        proc.send_signal(signal.CTRL_BREAK_EVENT)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def cmd_dev(_: argparse.Namespace) -> None:
    """Start API + UI together with the same root .env."""
    if not ROOT_ENV.is_file():
        print(f"Missing {ROOT_ENV}. Run: uv run scripts/run.py env", file=sys.stderr)
        raise SystemExit(1)

    env = _merged_env()
    secret = env.get("AUTHJWT_SECRET", "")
    print(f"Using AUTHJWT_SECRET from root .env (len={len(secret)})")
    print("Starting API :8000 and UI :8501 — Ctrl+C stops both")

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    api_cmd = [
        "uv",
        "run",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--app-dir",
        "src",
    ]
    ui_cmd = [
        "uv",
        "run",
        "streamlit",
        "run",
        "src/ui/app.py",
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1",
    ]

    api_proc = subprocess.Popen(
        api_cmd,
        cwd=API,
        env=env,
        creationflags=creationflags,
    )
    ui_proc = subprocess.Popen(
        ui_cmd,
        cwd=UI,
        env=env,
        creationflags=creationflags,
    )

    try:
        while True:
            api_code = api_proc.poll()
            ui_code = ui_proc.poll()
            if api_code is not None:
                print(f"API exited with code {api_code}", file=sys.stderr)
                break
            if ui_code is not None:
                print(f"UI exited with code {ui_code}", file=sys.stderr)
                break
            time.sleep(0.4)
    except KeyboardInterrupt:
        print("\nStopping…")
    finally:
        _terminate(ui_proc)
        _terminate(api_proc)

    raise SystemExit(api_proc.returncode or ui_proc.returncode or 0)


def cmd_test(_: argparse.Namespace) -> None:
    env = _merged_env()
    code = _uv("run", "pytest", cwd=API, check=False, env=env)
    code |= _uv("run", "pytest", cwd=UI, check=False, env=env)
    raise SystemExit(code)


def cmd_lint(_: argparse.Namespace) -> None:
    env = _merged_env()
    code = _uv("run", "ruff", "check", ".", cwd=API, check=False, env=env)
    code |= _uv("run", "ruff", "check", "src", "scripts", cwd=UI, check=False, env=env)
    raise SystemExit(code)


def cmd_setup(args: argparse.Namespace) -> None:
    cmd_env(args)
    cmd_install(args)
    cmd_infra_up(args)
    cmd_migrate(args)
    cmd_seed_test(args)
    print()
    print("Setup complete.")
    print("  uv run scripts/run.py dev")
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
        "dev": cmd_dev,
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

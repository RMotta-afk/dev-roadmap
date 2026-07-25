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
    """Postgres + Qdrant only (no API container — free :8000 for local API)."""
    _run(["docker", "compose", "up", "-d", "postgres", "qdrant"], env=_merged_env())
    # Avoid port clash if an old API container is still up
    _run(
        ["docker", "compose", "stop", "api"],
        env=_merged_env(),
        check=False,
    )


def cmd_api_docker(_: argparse.Namespace) -> None:
    """Build/start API (+ postgres, qdrant) in Docker. Prefer `dev` for local API testing."""
    env = _merged_env()
    secret = env.get("AUTHJWT_SECRET", "")
    print(f"Building API image with AUTHJWT_SECRET len={len(secret)} (from root .env)")
    _run(
        ["docker", "compose", "up", "-d", "--build", "postgres", "qdrant", "api"],
        env=env,
    )
    print()
    print("API:  http://localhost:8000/healthz")
    print("Logs: docker compose logs -f api")
    print("UI:   uv run scripts/run.py ui")


def cmd_infra_down(_: argparse.Namespace) -> None:
    _run(["docker", "compose", "down"], env=_merged_env())


def _local_app_env() -> dict[str, str]:
    """Root .env + paths that work when cwd is apps/api or apps/ui."""
    env = _merged_env()
    # Absolute so apps/api cwd still finds repo roadmaps
    env["BASE_ROADMAP_PATH"] = str(ROOT / "docs" / "archives")
    # Local processes talk to Docker-published ports on the host
    if not env.get("QDRANT_URL") or "qdrant:" in env.get("QDRANT_URL", ""):
        env["QDRANT_URL"] = "http://localhost:6333"
    if not env.get("API_BASE_URL") or "://api:" in env.get("API_BASE_URL", ""):
        env["API_BASE_URL"] = "http://localhost:8000"
    # Local API/UI expect host Postgres port, not docker service hostname
    db = env.get("DATABASE_URL", "")
    if "@postgres:" in db:
        env["DATABASE_URL"] = db.replace("@postgres:", "@localhost:")
    return env


def cmd_migrate(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/migrate.py", cwd=UI, env=_merged_env())


def cmd_seed_test(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/seed_test_user.py", cwd=UI, env=_merged_env())


def cmd_seed_admin(_: argparse.Namespace) -> None:
    _uv("run", "python", "scripts/create_user.py", "--admin", cwd=UI, env=_merged_env())


def cmd_seed_qdrant(args: argparse.Namespace) -> None:
    """Seed roadmap_nodes in local Qdrant (Docker on :6333)."""
    env = _local_app_env()
    cmd = ["run", "python", "scripts/seed_qdrant.py"]
    if getattr(args, "force", False):
        cmd.append("--force")
    print(f"Seeding Qdrant from {env.get('BASE_ROADMAP_PATH')} …")
    _uv(*cmd, cwd=API, env=env)


def cmd_api(_: argparse.Namespace) -> None:
    env = _local_app_env()
    print(
        f"Local API :8000  AUTHJWT_SECRET len={len(env.get('AUTHJWT_SECRET', ''))}  "
        f"QDRANT={env.get('QDRANT_URL')}  ROADMAP={env.get('BASE_ROADMAP_PATH')}"
    )
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
        env=env,
    )


def cmd_api_debug(_: argparse.Namespace) -> None:
    """Local API under debugpy (no reload — breakpoints work). Port 5678 attach-ready."""
    env = _local_app_env()
    print(
        f"API debug :8000  debugpy :5678  AUTHJWT_SECRET len={len(env.get('AUTHJWT_SECRET', ''))}"
    )
    print("In Cursor/VS Code: Run and Debug → 'API debug'  OR attach to 5678")
    print("Breakpoints: apps/api/src/app/auth.py  get_current_user / decode_access_token")
    # No --reload: child process breaks debugger attachment
    _uv(
        "run",
        "python",
        "-m",
        "debugpy",
        "--listen",
        "5678",
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--app-dir",
        "src",
        cwd=API,
        env=env,
    )


def cmd_ui(_: argparse.Namespace) -> None:
    env = _local_app_env()
    print(f"Local UI :8501  API_BASE_URL={env.get('API_BASE_URL')}")
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
        env=env,
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
    """Infra in Docker; local API + UI with the same root .env."""
    if not ROOT_ENV.is_file():
        print(f"Missing {ROOT_ENV}. Run: uv run scripts/run.py env", file=sys.stderr)
        raise SystemExit(1)

    print("Ensuring Postgres + Qdrant are up (Docker); stopping container API if any…")
    cmd_infra_up(argparse.Namespace())

    env = _local_app_env()
    secret = env.get("AUTHJWT_SECRET", "")
    print(f"Using AUTHJWT_SECRET from root .env (len={len(secret)})")
    print("Starting local API :8000 and UI :8501 — Ctrl+C stops both")

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
        "api-docker": cmd_api_docker,
        "migrate": cmd_migrate,
        "seed-test": cmd_seed_test,
        "seed-admin": cmd_seed_admin,
        "seed-qdrant": cmd_seed_qdrant,
        "api": cmd_api,
        "api-debug": cmd_api_debug,
        "ui": cmd_ui,
        "dev": cmd_dev,
        "test": cmd_test,
        "lint": cmd_lint,
        "setup": cmd_setup,
    }

    for name in handlers:
        p = sub.add_parser(name)
        if name == "seed-qdrant":
            p.add_argument(
                "--force",
                action="store_true",
                help="Drop and re-seed roadmap_nodes",
            )

    args = parser.parse_args()
    handlers[args.command](args)


if __name__ == "__main__":
    main()

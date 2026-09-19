"""Cross-platform lifecycle management for checkout-service-demo."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def repo_path() -> Path:
    configured = os.environ.get("DEMO_REPO_LOCAL_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "checkout-service-demo").resolve()


def python_path(repo: Path) -> Path:
    candidates = [
        repo / ".venv" / "Scripts" / "python.exe",
        repo / ".venv" / "bin" / "python",
    ]
    return next((path for path in candidates if path.exists()), Path(sys.executable))


def pid_file(repo: Path) -> Path:
    return repo / "logs" / "service.pid"


def read_pid(repo: Path) -> int | None:
    try:
        return int(pid_file(repo).read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def process_running(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and f'"{pid}"' in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop(repo: Path) -> bool:
    pid = read_pid(repo)
    if not pid:
        return False
    if process_running(pid):
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                if not process_running(pid):
                    break
                time.sleep(0.1)
    pid_file(repo).unlink(missing_ok=True)
    return True


def wait_for_health(port: int, process: subprocess.Popen[bytes]) -> None:
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(50):
        if process.poll() is not None:
            raise RuntimeError(f"checkout service exited with code {process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"checkout service did not become healthy at {url}")


def start(repo: Path, port: int) -> int:
    existing = read_pid(repo)
    if existing and process_running(existing):
        raise RuntimeError(f"checkout service is already running as PID {existing}")

    logs = repo / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    output_path = logs / "service.out.log"
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        start_new_session = True

    with output_path.open("ab") as output:
        process = subprocess.Popen(
            [str(python_path(repo)), "-m", "uvicorn", "app.main:app", "--port", str(port)],
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            start_new_session=start_new_session,
            close_fds=True,
        )
    pid_file(repo).write_text(str(process.pid), encoding="utf-8")
    try:
        wait_for_health(port, process)
    except Exception:
        pid_file(repo).unlink(missing_ok=True)
        raise
    return process.pid


def restart(repo: Path, port: int) -> int:
    stop(repo)
    return start(repo, port)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "restart", "status"])
    parser.add_argument("--port", type=int, default=int(os.environ.get("DEMO_PORT", "8000")))
    args = parser.parse_args()
    repo = repo_path()

    if args.action == "stop":
        stopped = stop(repo)
        print("Service stopped." if stopped else "No tracked service process was running.")
    elif args.action == "start":
        print(f"Service started as PID {start(repo, args.port)} on port {args.port}.")
    elif args.action == "restart":
        print(f"Service restarted as PID {restart(repo, args.port)} on port {args.port}.")
    else:
        pid = read_pid(repo)
        print({"pid": pid, "running": bool(pid and process_running(pid)), "repo": str(repo)})


if __name__ == "__main__":
    main()

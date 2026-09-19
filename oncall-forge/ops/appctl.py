"""Start, stop, or restart the demo checkout service (works on Windows and POSIX).

Usage: python appctl.py start|stop|restart
Reads DEMO_REPO_LOCAL_PATH from the environment or oncall-forge/.env, and
DEMO_PORT (default 8000).
"""

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def demo_repo() -> Path:
    path = os.environ.get("DEMO_REPO_LOCAL_PATH")
    if not path and ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEMO_REPO_LOCAL_PATH="):
                path = line.split("=", 1)[1].strip()
    if not path:
        sys.exit("DEMO_REPO_LOCAL_PATH is not set (environment or oncall-forge/.env)")
    return Path(path).resolve()


def demo_port() -> int:
    return int(os.environ.get("DEMO_PORT", "8000"))


def pids_on_port(port: int) -> set[int]:
    if os.name == "nt":
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
        pids = set()
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[3] == "LISTENING" and parts[1].endswith(f":{port}"):
                pids.add(int(parts[4]))
        return pids
    out = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True, text=True).stdout
    return {int(p) for p in out.split()}


def stop() -> None:
    port = demo_port()
    for pid in pids_on_port(port):
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
    deadline = time.time() + 10
    while pids_on_port(port) and time.time() < deadline:
        time.sleep(0.2)


def start() -> None:
    repo, port = demo_repo(), demo_port()
    (repo / "logs").mkdir(exist_ok=True)
    out = open(repo / "logs" / "uvicorn.out", "ab")
    flags = {}
    if os.name == "nt":
        flags["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        flags["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=repo, stdin=subprocess.DEVNULL, stdout=out, stderr=out, **flags,
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            return
        except OSError:
            time.sleep(0.3)
    sys.exit(f"demo service did not become healthy on port {port}")


def restart() -> None:
    stop()
    start()


if __name__ == "__main__":
    actions = {"start": start, "stop": stop, "restart": restart}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        sys.exit(__doc__)
    actions[sys.argv[1]]()

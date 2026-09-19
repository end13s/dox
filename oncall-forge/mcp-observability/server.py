"""oncall-observability: a FastMCP server exposing read access to the
checkout-service-demo's metrics, logs, and deploy history, plus a single
gated write action (restart_service).

Run: python server.py
Serves streamable HTTP at http://localhost:8765/mcp
"""

import os
import re
import sys
from pathlib import Path

import httpx
from fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ops"))
import appctl  # noqa: E402

DEMO_URL = os.environ.get("DEMO_SERVICE_URL", "http://localhost:8000")
DEMO_REPO = appctl.demo_repo()
APP_LOG = DEMO_REPO / "logs" / "app.log"
DEPLOYS_LOG = DEMO_REPO / "logs" / "deploys.log"

LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "WARNING": 30, "ERROR": 40}
ENTRY_START = re.compile(r"^\d{4}-\d{2}-\d{2}T\S+ (\w+) ")

mcp = FastMCP("oncall-observability")


def _tail_text(path: Path, max_bytes: int = 512_000) -> str:
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    return text.split("\n", 1)[1] if size > max_bytes and "\n" in text else text


@mcp.tool
def get_error_rate(window_s: int = 60) -> dict:
    """Get the checkout service's error rate over the last window_s seconds."""
    resp = httpx.get(f"{DEMO_URL}/metrics", params={"window_s": window_s}, timeout=5)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def get_recent_logs(level: str = "ERROR", limit: int = 50) -> list[str]:
    """Get the most recent log entries at or above the given level (DEBUG, INFO, WARN, ERROR).

    Each entry is one log record including its stack trace lines, if any.
    """
    if not APP_LOG.exists():
        return []
    threshold = LEVELS.get(level.upper(), LEVELS["ERROR"])
    entries: list[tuple[str, list[str]]] = []
    for line in _tail_text(APP_LOG).splitlines():
        match = ENTRY_START.match(line)
        if match:
            entries.append((match.group(1), [line]))
        elif entries:
            entries[-1][1].append(line)
    kept = ["\n".join(lines) for lvl, lines in entries if LEVELS.get(lvl, 0) >= threshold]
    return kept[-limit:]


@mcp.tool
def get_recent_deploys(limit: int = 5) -> list[str]:
    """Get the most recent deploys as '<sha> <utc time> <commit subject>'."""
    if not DEPLOYS_LOG.exists():
        return []
    return DEPLOYS_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]


@mcp.tool
def restart_service() -> dict:
    """Restart the checkout service. Approval-gated in TrueForge."""
    appctl.restart()
    return {"restarted": True}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)

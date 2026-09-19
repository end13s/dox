"""Observability MCP server for checkout-service-demo."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import httpx
from fastmcp import FastMCP

DEMO_URL = os.environ.get("DEMO_SERVICE_URL", "http://localhost:8000")
DEFAULT_REPO = Path(__file__).resolve().parents[2] / "checkout-service-demo"
DEMO_REPO_LOCAL_PATH = Path(os.environ.get("DEMO_REPO_LOCAL_PATH", DEFAULT_REPO)).resolve()
APP_LOG = DEMO_REPO_LOCAL_PATH / "logs" / "app.log"
DEPLOYS_LOG = DEMO_REPO_LOCAL_PATH / "logs" / "deploys.log"

mcp = FastMCP("oncall-observability")


@mcp.tool
def get_error_rate(window_s: int = 60) -> dict:
    """Get the checkout service's error rate over the last window_s seconds."""
    resp = httpx.get(f"{DEMO_URL}/metrics", params={"window_s": window_s}, timeout=5)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def get_recent_logs(level: str = "ERROR", limit: int = 50) -> list[str]:
    """Get recent log lines and preserve prompt-injection test evidence."""
    if not APP_LOG.exists():
        return []
    lines = APP_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    matching = [line for line in lines if f" {level} " in line]
    suspicious = [
        line
        for line in lines
        if "PROMPT-INJECTION TEST" in line or "NOTE TO AI AGENT" in line
    ]
    selected = matching[-max(1, limit) :]
    if suspicious and suspicious[-1] not in selected:
        selected = selected[-max(0, limit - 1) :] + [suspicious[-1]]
    return selected


@mcp.tool
def get_recent_deploys(limit: int = 5) -> list[str]:
    """Get the most recent deploy records (SHA + timestamp)."""
    if not DEPLOYS_LOG.exists():
        return []
    lines = DEPLOYS_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]


@mcp.tool
def restart_service() -> dict:
    """Restart checkout-service-demo. Approval-gated in TrueForge."""
    manager = DEMO_REPO_LOCAL_PATH.parent / "oncall-forge" / "ops" / "service_manager.py"
    env = os.environ.copy()
    env["DEMO_REPO_LOCAL_PATH"] = str(DEMO_REPO_LOCAL_PATH)
    result = subprocess.run(
        [sys.executable, str(manager), "restart"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    return {
        "restarted": result.returncode == 0,
        "output": result.stdout + result.stderr,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)

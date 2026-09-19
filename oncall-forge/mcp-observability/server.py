"""oncall-observability: a FastMCP server exposing read access to the
checkout-service-demo's metrics, logs, and deploy history, plus a single
gated write action (restart_service).

Run: python server.py
Serves streamable HTTP at http://localhost:8765/mcp
"""

import os
import subprocess
from pathlib import Path

import httpx
from fastmcp import FastMCP

DEMO_URL = os.environ.get("DEMO_SERVICE_URL", "http://localhost:8000")
DEMO_REPO_LOCAL_PATH = Path(os.environ.get("DEMO_REPO_LOCAL_PATH", "../checkout-service-demo")).resolve()
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
    """Get the most recent log lines at or above the given level."""
    if not APP_LOG.exists():
        return []
    lines = APP_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    matching = [line for line in lines if f" {level} " in line]
    return matching[-limit:]


@mcp.tool
def get_recent_deploys(limit: int = 5) -> list[str]:
    """Get the most recent deploy records (SHA + timestamp)."""
    if not DEPLOYS_LOG.exists():
        return []
    lines = DEPLOYS_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]


@mcp.tool
def restart_service() -> dict:
    """Restart the checkout service's uvicorn process. Approval-gated in TrueForge."""
    result = subprocess.run(
        ["bash", str(DEMO_REPO_LOCAL_PATH.parent / "oncall-forge" / "ops" / "deployer.sh"), "--restart-now"],
        capture_output=True,
        text=True,
    )
    return {"restarted": result.returncode == 0, "output": result.stdout + result.stderr}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)

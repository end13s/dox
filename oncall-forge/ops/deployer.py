"""Poll origin/main and restart checkout-service-demo after each deployment."""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone

from service_manager import repo_path, restart


def git(repo, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main() -> None:
    repo = repo_path()
    port = int(os.environ.get("DEMO_PORT", "8000"))
    interval = int(os.environ.get("DEPLOY_POLL_SECONDS", "5"))
    deploy_log = repo / "logs" / "deploys.log"
    deploy_log.parent.mkdir(parents=True, exist_ok=True)
    last_sha: str | None = None

    print(f"Watching origin/main for {repo} every {interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            git(repo, "fetch", "origin", "main", "--quiet")
            new_sha = git(repo, "rev-parse", "origin/main")
            if new_sha != last_sha:
                git(repo, "reset", "--hard", "origin/main", "--quiet")
                pid = restart(repo, port)
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                with deploy_log.open("a", encoding="utf-8") as handle:
                    handle.write(f"{new_sha} {timestamp}\n")
                print(f"Deployed {new_sha[:12]} at {timestamp}; service PID {pid}.", flush=True)
                last_sha = new_sha
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Deployer stopped.")


if __name__ == "__main__":
    main()

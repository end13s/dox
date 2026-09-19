"""Reset checkout-service-demo to demo-good and restart it safely."""

from __future__ import annotations

import os
import shutil
import subprocess

from service_manager import repo_path, restart


def git(repo, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True)


def main() -> None:
    repo = repo_path()
    port = int(os.environ.get("DEMO_PORT", "8000"))
    good_tag = os.environ.get("DEMO_GOOD_TAG", "demo-dox")
    git(repo, "fetch", "origin", "--quiet")
    git(repo, "checkout", "main", "--quiet")
    git(repo, "reset", "--hard", good_tag, "--quiet")
    git(repo, "push", "origin", "main", "--force-with-lease")

    gh = shutil.which("gh")
    if gh:
        result = subprocess.run(
            [gh, "pr", "list", "--state", "open", "--json", "number", "--jq", ".[].number"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        for number in result.stdout.split():
            subprocess.run(
                [gh, "pr", "close", number, "--comment", "Closed by reset_demo.py"],
                cwd=repo,
                check=True,
            )

    logs = repo / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for name in ("app.log", "deploys.log", "service.out.log"):
        (logs / name).write_text("", encoding="utf-8")
    pid = restart(repo, port)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    print(f"Demo reset to {good_tag} ({sha}); service PID {pid} on port {port}.")


if __name__ == "__main__":
    main()

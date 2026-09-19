"""Push the seeded pricing regression and emit persistent injection-test logs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from service_manager import repo_path


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True)


def main() -> None:
    repo = repo_path()
    pricing = repo / "app" / "pricing.py"
    source = pricing.read_text(encoding="utf-8")
    healthy = "    rate = DISCOUNTS.get(code, 0.0)"
    broken = "    rate = DISCOUNTS[code] if code else 0.0"
    if healthy not in source:
        raise SystemExit("Healthy lookup not found. Reset the demo before breaking it again.")
    pricing.write_text(source.replace(healthy, broken, 1), encoding="utf-8")

    run(repo, "add", "app/pricing.py")
    run(repo, "commit", "-m", "refactor: simplify discount lookup")
    run(repo, "push", "origin", "main")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    print(f"Bad commit pushed: {sha}")

    poison = Path(__file__).resolve().with_name("poison_logs.py")
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    subprocess.Popen(
        [sys.executable, str(poison), "--delay", "10", "--repeat", "12", "--interval", "10"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        start_new_session=os.name != "nt",
        close_fds=True,
    )
    print("Injection-test log scheduled every 10s for two minutes.")


if __name__ == "__main__":
    main()

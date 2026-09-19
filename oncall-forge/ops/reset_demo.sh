#!/usr/bin/env bash
# Resets the demo repo to a clean state between takes: force-resets main to
# the demo-good tag, closes any open PRs, clears logs, and restarts the app.
# Test this 3x — every demo take depends on it.
set -euo pipefail

DEMO_REPO_PATH="${DEMO_REPO_LOCAL_PATH:-../checkout-service-demo}"
PORT="${DEMO_PORT:-8000}"
PID_FILE="/tmp/checkout-service-demo.pid"

cd "$DEMO_REPO_PATH"

git fetch origin --quiet
git checkout main --quiet
git reset --hard demo-good --quiet
git push origin main --force

# Close any open PRs left over from a previous take (requires GitHub CLI: gh).
if command -v gh >/dev/null 2>&1; then
  for pr in $(gh pr list --state open --json number --jq '.[].number'); do
    gh pr close "$pr" --comment "Closed by reset_demo.sh"
  done
fi

: > logs/app.log
: > logs/deploys.log

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  kill "$(cat "$PID_FILE")"
fi
nohup uvicorn app.main:app --port "$PORT" >/dev/null 2>&1 &
echo $! > "$PID_FILE"

echo "Demo reset to $(git rev-parse HEAD) and restarted on port $PORT."

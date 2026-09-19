#!/usr/bin/env bash
# Polls the demo repo's main branch. On a new commit SHA, pulls, restarts
# uvicorn, and appends a record to logs/deploys.log.
#
# Usage: ./deployer.sh            # run the poll loop
#        ./deployer.sh --restart-now   # restart immediately, no pull (used by restart_service tool)
set -euo pipefail

DEMO_REPO_PATH="${DEMO_REPO_LOCAL_PATH:-../checkout-service-demo}"
PORT="${DEMO_PORT:-8000}"
PID_FILE="/tmp/checkout-service-demo.pid"
LOG_FILE="$DEMO_REPO_PATH/logs/deploys.log"

mkdir -p "$DEMO_REPO_PATH/logs"

restart_app() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    kill "$(cat "$PID_FILE")"
  fi
  ( cd "$DEMO_REPO_PATH" && nohup uvicorn app.main:app --port "$PORT" >/dev/null 2>&1 & echo $! > "$PID_FILE" )
}

if [[ "${1:-}" == "--restart-now" ]]; then
  restart_app
  exit 0
fi

last_sha=""
while true; do
  cd "$DEMO_REPO_PATH"
  git fetch origin main --quiet
  new_sha="$(git rev-parse origin/main)"
  if [[ "$new_sha" != "$last_sha" ]]; then
    git reset --hard origin/main --quiet
    restart_app
    echo "$new_sha $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG_FILE"
    last_sha="$new_sha"
  fi
  cd - >/dev/null
  sleep 10
done

#!/usr/bin/env bash
# Auto-deploy: polls origin/main of the demo repo every 10s. On a new commit it
# resets the working copy, restarts the service, and appends
# "<sha> <utc time> <commit subject>" to logs/deploys.log.
# Run from Git Bash. Don't also run uvicorn by hand; this owns the service.
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

LOG_FILE="$DEMO_REPO_LOCAL_PATH/logs/deploys.log"
mkdir -p "$DEMO_REPO_LOCAL_PATH/logs"
echo "deployer watching origin/main of $DEMO_REPO_LOCAL_PATH"

last_sha=""
while true; do
  if git -C "$DEMO_REPO_LOCAL_PATH" fetch origin main --quiet; then
    new_sha="$(git -C "$DEMO_REPO_LOCAL_PATH" rev-parse origin/main)"
    if [[ "$new_sha" != "$last_sha" ]]; then
      git -C "$DEMO_REPO_LOCAL_PATH" reset --hard "$new_sha" --quiet
      python "$OPS_DIR/appctl.py" restart
      subject="$(git -C "$DEMO_REPO_LOCAL_PATH" log -1 --format=%s "$new_sha")"
      echo "$new_sha $(date -u +%Y-%m-%dT%H:%M:%SZ) $subject" >> "$LOG_FILE"
      echo "deployed $new_sha ($subject)"
      last_sha="$new_sha"
    fi
  fi
  sleep 10
done

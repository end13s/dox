#!/usr/bin/env bash
# Resets the demo between takes: force main back to the demo-good tag, close
# open PRs (and delete their branches), clear logs, restart the service.
# Run from Git Bash. Test this 3x: every demo take depends on it.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

GH="$(command -v gh || true)"
if [[ -z "$GH" && -x "/c/Program Files/GitHub CLI/gh.exe" ]]; then
  GH="/c/Program Files/GitHub CLI/gh.exe"
fi

python "$OPS_DIR/appctl.py" stop

cd "$DEMO_REPO_LOCAL_PATH"
git fetch origin --tags --quiet
git checkout main --quiet
git reset --hard demo-good --quiet
git push origin main --force --quiet

if [[ -n "$GH" ]]; then
  for pr in $("$GH" pr list --state open --json number --jq '.[].number' | tr -d '\r'); do
    "$GH" pr close "$pr" --delete-branch --comment "Closed by reset_demo.sh"
  done
else
  echo "gh not found: close leftover PRs by hand" >&2
fi

mkdir -p logs
: > logs/app.log
: > logs/deploys.log

python "$OPS_DIR/appctl.py" start
echo "demo reset to $(git rev-parse --short HEAD) and running on port ${DEMO_PORT:-8000}"

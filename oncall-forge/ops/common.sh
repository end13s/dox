#!/usr/bin/env bash
# Sourced by the other ops scripts. Run them from Git Bash, not WSL bash.
OPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${DEMO_REPO_LOCAL_PATH:-}" && -f "$OPS_DIR/../.env" ]]; then
  DEMO_REPO_LOCAL_PATH="$(grep -E '^DEMO_REPO_LOCAL_PATH=' "$OPS_DIR/../.env" | head -1 | cut -d= -f2- | tr -d '\r')"
fi
: "${DEMO_REPO_LOCAL_PATH:?set DEMO_REPO_LOCAL_PATH in oncall-forge/.env}"
export DEMO_REPO_LOCAL_PATH

# reset/break run destructive git commands, so refuse any other repo.
if ! git -C "$DEMO_REPO_LOCAL_PATH" remote get-url origin 2>/dev/null | grep -q "checkout-service-demo"; then
  echo "refusing to run: $DEMO_REPO_LOCAL_PATH is not a checkout-service-demo clone" >&2
  exit 1
fi

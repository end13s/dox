#!/usr/bin/env bash
# Pushes the seeded bug to the demo repo's main branch, then triggers the
# poisoned log line ~20s later to simulate an attempted prompt injection
# mid-incident.
set -euo pipefail

DEMO_REPO_PATH="${DEMO_REPO_LOCAL_PATH:-../checkout-service-demo}"

cd "$DEMO_REPO_PATH"

python - <<'PYEOF'
from pathlib import Path

path = Path("app/pricing.py")
src = path.read_text()
src = src.replace(
    "    rate = DISCOUNTS.get(code, 0.0)",
    "    rate = DISCOUNTS[code] if code else 0.0",
)
path.write_text(src)
PYEOF

git add app/pricing.py
git commit -m "refactor: simplify discount lookup"
git push origin main

echo "Bad commit pushed: $(git rev-parse HEAD)"

( sleep 20 && python "$(dirname "$0")/poison_logs.py" ) &

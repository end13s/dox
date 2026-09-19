#!/usr/bin/env bash
# Pushes the seeded bug to main of the demo repo, then starts the poisoned log
# lines ~20s later. Run from Git Bash with deployer.sh running so it deploys.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

cd "$DEMO_REPO_LOCAL_PATH"
git checkout main --quiet

python - <<'PYEOF'
import sys
from pathlib import Path

path = Path("app/pricing.py")
src = path.read_text()
old = "    rate = DISCOUNTS.get(code, 0.0)"
if old not in src:
    sys.exit("pricing.py is already broken (or changed); run reset_demo.sh first")
path.write_text(src.replace(old, "    rate = DISCOUNTS[code]"))
PYEOF

git add app/pricing.py
git commit -q -m "refactor: simplify discount lookup"
git push origin main --quiet
echo "bad commit pushed: $(git rev-parse --short HEAD)"

( sleep 20; python "$OPS_DIR/poison_logs.py" ) >/dev/null 2>&1 &
disown

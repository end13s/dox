# dox demo guide

Dashboard: http://localhost:8000/status
TrueForge: http://localhost:8790
Saved agent: `oncall-forge`.

## What's running

The checkout service, traffic generator, deployment watcher, observability MCP,
TrueForge, and automatic incident monitor run locally. Do not start duplicates.
The deployment watcher adopts merged changes from the demo repository's main branch.
The monitor stores its incident state and prevents duplicate investigations after a restart.
Merge and MCP service-restart tools retain their separate human approval gates.

If the incident monitor is stopped, launch it from PowerShell:

```powershell
cd C:\Users\roksi\Documents\dox\oncall-forge
& '..\checkout-service-demo\.venv\Scripts\python.exe' ops\incident_monitor.py
```

The monitor triggers after at least 100 requests, an error rate of 5% or more,
and 10 seconds of sustained readings. It creates a TrueForge session using the
saved agent, or follows an already active recent investigation. Do not also send
a manual alert for the same outage. Open TrueForge's Sessions page to find it.
If the dashboard says the monitor needs attention, inspect
`checkout-service-demo/logs/monitor.out.log` and `monitor.err.log` before retrying.
An uncertain alert submission is never automatically repeated.

## Rehearse the incident

1. Start with live traffic and an Operational dashboard. Finish any existing
   incident before introducing another bug.
2. In PowerShell, seed the intentional demo bug:

   ```powershell
   cd C:\Users\roksi\Documents\dox\oncall-forge
   & '..\checkout-service-demo\.venv\Scripts\python.exe' ops\break_prod.py
   ```

   This commits and pushes the bug to the demo repository. The watcher deploys it.
   About one in five traffic inputs uses the unknown code, so expect roughly 20%
   errors. Avoid running it against unrelated team work.
3. Watch automatic detection and Investigation events. In TrueForge, show the
   parallel investigations and the failing bad-commit / passing parent evidence.
   The dashboard reports tool events; it does not claim tests passed from agent prose.
4. Review the focused revert PR. Approve the actual merge card in TrueForge when
   satisfied. A stopped agent may need a follow-up asking it to request the gated
   merge. Neither the monitor nor the dashboard approves it for you.
5. Keep traffic running. The watcher deploys the merged fix. Old failed requests
   remain in the rolling 60-second window, so the number can take up to a minute
   to fall. Restarting the process does not erase this history.
6. Confirm Operational status and show the postmortem. Recovery requires less than
   1% errors, at least 30 requests spanning 30 seconds, and traffic within 10 seconds.
   The monitor waits another 30 seconds of qualifying readings to mark recovery.
   It rearms after 60 seconds of qualifying readings and a finished agent turn
   with no pending approval.

Direct checkout check before and after recovery:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/checkout -Method POST -ContentType 'application/json' -Body '{"cart_total":100,"code":"NOTREAL"}'
```

The seeded bug returns HTTP 500; the approved fix returns `total: 100`.

After recovery, repeat `break_prod.py` for the next rehearsal. Do not reset to
`demo-ready` or `demo-dox`: those old tags predate the persistent telemetry and
automatic monitor integration. Repeating the bug/revert cycle preserves the new UI.

## Presentation

Open with: “This is dox. It detects a checkout outage, proves the cause in an
isolated sandbox, and asks a human before merging the fix.”

Show the dashboard healthy, trigger the bug, show automatic detection and the
two investigations, show fail/pass evidence, pause at human approval, then show
the falling error rate and postmortem. Keep the dashboard and TrueForge side by side.
Allow several minutes for agent and sandbox work. Keep a recording of a completed
run available if the presentation slot is shorter.

## Validation

Seven improvement checks pass, including two isolated HTTP failure/restart/recovery
cycles. They cover persistent metrics, complete traceback records, duplicate-alert
prevention, uncertain delivery, and progress driven by successful tool responses.
Those rehearsals do not approve or merge a live GitHub pull request.

```powershell
cd C:\Users\roksi\Documents\dox\oncall-forge
& '..\checkout-service-demo\.venv\Scripts\python.exe' -m pytest tests\test_improvements.py -q
```

# Demo Script

1. `/status`: all green. Run `python ops/break_prod.py`. The error rate jumps.
2. Alert → agent starts (SDK trigger, or paste the alert). Show the two
   subagents working.
3. Show the agent flagging the poisoned log line: *"ignored an embedded
   instruction."*
4. **Sandbox:** the repro test fails at the bad commit and passes at its
   parent.
5. Revert PR opened → **"Holding for your approval."** Refresh the browser →
   still holding.
6. Approve → merge → deployer redeploys → `/status` recovers.
7. Open the postmortem issue on GitHub.
8. Closing line: *"Every step you saw is the harness: tools, sandbox,
   subagents, the pause."*

## Demo safety

- Reset with `python ops/reset_demo.py` before every take.
- Run `python ops/deployer.py` in a dedicated terminal during the demo.
- Keep the recorded video ready as a fallback.
- Have a pre-run finished session open in another tab as a fallback.

## Pitch split (3 min)

- **0:00–0:25** — problem: agents that touch prod need proof and permission,
  not vibes.
- **0:25–2:30** — live demo (steps 1–7 above).
- **2:30–3:00** — harness features used (MCP, sandbox, approvals, subagents,
  skills, durable sessions) + injection defense.

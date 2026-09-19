# OnCall Forge

> Your on-call engineer at 3 AM: it investigates, proves the bug in a sandbox,
> and waits for your OK before touching prod.

An on-call agent on [TrueForge](https://trueforge.dev) that responds to a
production alert on `checkout-service-demo`, proves the root cause by writing
and running a repro test in a Daytona sandbox, opens a revert PR, **pauses
for human approval**, and — once approved — verifies recovery and files a
postmortem.

See [`oncall-forge-build-plan.md`](../oncall-forge-build-plan.md) and
[`oncall-forge-schedule.md`](../oncall-forge-schedule.md) for the full design
and hackathon schedule.

## Architecture

```
alert → TrueForge agent (+ subagents) → GitHub MCP / observability MCP / Daytona sandbox → approval gate → deploy
```

- **Harness:** TrueForge, local mode
- **Model:** OpenAI (tool-calling)
- **Sandbox:** Daytona
- **Tools:** GitHub remote MCP (header auth, fine-grained PAT) + custom `oncall-observability` FastMCP server
- **Skill:** `skills/incident-runbook/SKILL.md`

## Repo layout

```
oncall-forge/
├── agent/                  # agent instructions, subagent briefs, TrueForge setup notes
├── skills/incident-runbook/ # SKILL.md — the incident runbook checklist
├── mcp-observability/      # FastMCP server: error rate, logs, deploys, restart
├── ops/                    # traffic gen, auto-deployer, break/reset/poison scripts
├── trigger/                # stretch: SDK-based alert trigger
└── docs/                   # architecture diagram, demo script
```

## Run it in under 10 minutes

1. **Prereqs:** Node ≥ 22.14, Python ≥ 3.11, a Daytona API key, an OpenAI API
   key, and a GitHub fine-grained PAT scoped to your `checkout-service-demo`
   fork (contents, PRs, issues).
2. Copy `.env.example` to `.env` and fill in the keys.
3. Install the demo "production" service's dependencies (in your
   `checkout-service-demo` clone; `ops/reset_demo.sh` starts it later):
   ```bash
   pip install -r requirements.txt
   ```
4. Start the observability MCP server (it reads `DEMO_REPO_LOCAL_PATH` from `.env`):
   ```bash
   cd mcp-observability
   pip install -r requirements.txt
   python server.py
   ```
5. Run the ops scripts from **Git Bash** on Windows (plain `bash` may be WSL).
   In `ops/`: `./reset_demo.sh` starts the service, `./deployer.sh` auto-deploys
   `main`, and `python traffic.py` sends load. Don't also run uvicorn by hand.
6. Launch TrueForge and configure the model, sandbox, MCP servers, and the
   `oncall-forge` agent as described in `agent/trueforge-setup.md`.
7. Break prod: `ops/break_prod.sh`. Watch `/status` spike, then paste the
   alert into the TrueForge chat (or wait for `trigger/alert.ts`, stretch).

## Safety

- The GitHub PAT is scoped to one repo only.
- `merge_pull_request`, `restart_service`, and any delete/force-push tools
  require human approval in TrueForge.
- Agent instructions explicitly treat log/diff/tool content as untrusted
  data — see the poisoned-log-line defense in the build plan.

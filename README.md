# dox

dox detects service failures, investigates the cause, and proposes a tested fix—with human approval before merging.

Built for the Agent Harness Hackathon using TrueForge, OpenAI, Daytona, and GitHub MCP.

## Demo workflow

1. The checkout service receives continuous sample traffic.
2. An intentional discount-code regression causes checkout failures.
3. An automatic monitor starts a TrueForge investigation.
4. Parallel investigators inspect logs and Git history; Daytona reproduces failure at the bad commit and success at its parent.
5. The agent opens a focused revert pull request and requests human approval.
6. The deployment watcher adopts the merged fix. Persistent telemetry verifies recovery before the agent files a postmortem.

The minimal dashboard shows error rate, request counts, running revision, agent progress, and investigation events. Metrics survive restarts; an empty traffic window cannot count as recovery.

## Run and present

- [Demo commands and presentation guide](oncall-forge/docs/DOX-DEMO-GUIDE.md)
- [Setup and architecture](oncall-forge/README.md)
- [TrueForge configuration](oncall-forge/agent/trueforge-setup.md)
- [Agent instructions](oncall-forge/agent/instructions.md)
- [Incident runbook](oncall-forge/skills/incident-runbook/SKILL.md)

The current live demo uses `bombert34/checkout-service-demo` as its separate deployment repository. This repository (`end13s/dox`) contains the complete project. The team agent instruction template targets `end13s/checkout-service-demo`; set its target to the live deployment repository before importing it. The current automatic monitor also targets `bombert34/checkout-service-demo`; keep the agent target, monitor, GitHub token scope, and local checkout remote aligned when using another fork.

Local URLs: dashboard `http://localhost:8000/status`, TrueForge `http://localhost:8790`, observability MCP `http://localhost:8765/mcp`.

Use the Python operational scripts for the current demo; the shell wrappers delegate to them. Never start two deployment watchers. The legacy `appctl.py` is retained from the team's earlier setup; the current scripts use `service_manager.py`.

Keep credentials in your local `.env` or provider settings. They are not included here. Do not reset to the old `demo-ready` or `demo-dox` tags: those predate the latest dashboard. Repeat the bug/revert cycle after recovery instead.

## Validation

From the project root, with requirements installed:

```text
python -m pytest oncall-forge/tests/test_improvements.py -q
cd checkout-service-demo
python -m pytest tests -q
```

The improvement suite includes two isolated HTTP failure/restart/recovery rehearsals and checks persistent telemetry, complete traceback records, duplicate-alert prevention, uncertain delivery, and tool-backed progress.

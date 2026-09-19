# TrueForge Setup — `oncall-forge` agent

Exact configuration steps. Add screenshots here as you go.

## 1. Models
- Add an OpenAI model with the API key from `.env`.
- Send a test message to confirm it responds.

## 2. Sandbox
- Add Daytona as the sandbox provider with the API key from `.env`.
- Smoke test: ask an agent to clone the public demo repo and run `pytest`.

## 3. MCP servers
- **GitHub remote MCP** — header auth, `Authorization: Bearer <GITHUB_PAT>`.
  Use TrueForge's catalog entry if one exists. Verify with "list recent
  commits on checkout-service-demo."
- **`oncall-observability`** — `http://localhost:8765/mcp`. Start
  `mcp-observability/server.py` first. Verify with `get_error_rate`.

## 4. Agent: `oncall-forge`
- **Tools enabled:**
  - GitHub: read commits/diffs, create branch, create PR, merge PR, create
    issue
  - Observability: `get_error_rate`, `get_recent_logs`, `get_recent_deploys`,
    `restart_service`
  - Sandbox (Daytona): clone/run
- **Require human approval on:** `merge_pull_request`, `restart_service`,
  and any delete / force-push tool if present. Prefer not enabling delete
  tools at all.
- **Subagents:** enable dynamic sub-agents (`config.dynamic_sub_agents`).
  The briefs live inside `instructions.md`; nothing to create separately.
- **Sandbox:** enable it on the agent (skills require it).
- **Skill:** `incident-runbook` (commit it first, then register it).
- **Instructions:** `agent/instructions.md` (paste as the system prompt).

## 5. Durability checks
- [ ] Refresh the browser while the agent is paused on approval — session
      state survives.
- [ ] Ctrl-C the TrueForge server while paused, restart it, and approve —
      note whether this works; demo whichever is more reliable.

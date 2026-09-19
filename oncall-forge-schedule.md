# OnCall Forge — Hackathon Schedule

**Project:** An on-call agent on TrueForge that investigates a production incident and proves the root cause by writing and running a repro test in the sandbox. It opens a revert PR, then **pauses for human approval** before merging. After the merge, the service recovers live, and the agent files a postmortem.

**Pitch line:** *"Your on-call engineer at 3 AM: it investigates, proves the bug in a sandbox, and waits for your OK before touching prod."*

> This schedule assumes build starts ~11:00 and submission is due ~5:30. **Shift all blocks to the real deadline.**

## Roles

| Person | Owns | Demo role |
|---|---|---|
| **Eduard** | TrueForge setup, agent instructions, approvals, subagents, skill, session durability | Drives the live demo |
| **Robert** | Demo "prod" service, bad commit, traffic generator, auto-deployer, observability MCP server, reset script | Architecture Q&A |
| **Aldi** | Sandbox repro flow, status page, SDK alert trigger (stretch), README, video, slides | Delivers the pitch |

---

## 11:00–11:45 · Setup gate — EVERYONE (nothing else until this is done)

| Eduard | Robert | Aldi |
|---|---|---|
| Node ≥ 22.14, `npx @truefoundry/trueforge@latest` running, OpenAI key connected, one chat works | Create public repo `checkout-service-demo` + project repo `oncall-forge` | **Daytona account + API key** (sandbox provider), connect it in TrueForge |
| GitHub fine-grained PAT scoped to the demo repo only | Scaffold the FastAPI app + a passing test | Test: agent clones the public demo repo in the sandbox and runs `pytest` |

**11:45 check:** a TrueForge agent can (1) call a tool and (2) run code in the sandbox. If the sandbox fails, grab a TrueFoundry mentor **immediately**, because it is our star feature.

## 11:45–1:30 · Foundations

| Eduard | Robert | Aldi |
|---|---|---|
| Connect GitHub MCP (header auth with PAT) | Demo app `/checkout` + `/status` (live error-rate page) | Refine the sandbox flow: clone → checkout commit → write repro test → run at `HEAD` and `HEAD~1` |
| Draft agent instructions + load `incident-runbook` skill | `traffic.py` constant load; `deployer.sh` auto-pulls `main` and restarts | Draft README skeleton |
| Mark destructive tools **require approval** | Observability MCP server: `get_error_rate`, `get_recent_logs`, `get_recent_deploys`, `restart_service` | |

### 1:30 · SYNC (10 min)
✅ Robert pushes the bad commit → error rate spikes on `/status` → Eduard's agent reads it through the observability MCP.

## 1:30–3:30 · Core build

| Eduard | Robert | Aldi |
|---|---|---|
| Full loop: investigate (subagents) → sandbox proof → open revert PR → **approval pause** → merge → verify recovery → postmortem issue | Poisoned log line (prompt injection) in the logs | Wire the sandbox step into Eduard's agent (skill instructions + prompts) |
| Test durability: refresh mid-approval, then **restart the TrueForge server** mid-approval | `reset_demo.sh`: force the demo repo back to a good state, close PRs, clear logs | Stretch: `trigger/alert.ts` (TrueForge SDK) auto-starts a session when error rate > threshold |

### 3:30 · SYNC + FEATURE FREEZE
✅ Full end-to-end run succeeds 2× in a row from `reset_demo.sh`. **Nothing new after this.**

## 3:30–4:30 · Harden the demo

| Eduard + Robert | Aldi |
|---|---|
| 3 more full runs; fix flaky prompts; lock model + temperature | Slides + architecture diagram |
| Pick the exact moments to show: subagents, sandbox output, the pause | Final README: clone → run in < 10 min, `.env.example`, no keys |

## 4:30–5:30 · Video, rehearsal, submit (NON-NEGOTIABLE)

| Time | Eduard | Robert | Aldi |
|---|---|---|---|
| 4:30 | Record the **3-min demo video**. Film the pause + refresh. | Scrub the repo for keys/personal data; check the video too | Finish slides |
| 4:50 | Rehearsal #1 (timed) | Rehearsal #1 | Rehearsal #1 |
| 5:05 | Rehearsal #2 | Prep answers to 3 judge questions | Rehearsal #2 |
| 5:20 | **SUBMIT** (public repo + video) | | |

### Pitch split (3 min)
- **0:00–0:25 Aldi:** problem: agents that touch prod need proof and permission, not vibes
- **0:25–2:30 Eduard:** live demo
  1. Break prod
  2. Agent investigates with subagents
  3. Sandbox proves the bad commit
  4. Revert PR → **pause** → refresh the page → still waiting
  5. Approve → recovery → postmortem
- **2:30–3:00 Aldi:** harness features used (MCP, sandbox, approvals, subagents, skills, durable sessions) + injection defense

### Likely judge questions (Robert)
1. What stops it from doing something destructive? → approval-gated tools, a PAT scoped to one repo, and injected instructions ignored.
2. Why the sandbox instead of just reading the diff? → proof over guessing; agent-written code never touches prod.
3. What if the server dies mid-incident? → the session persists (show or describe the restart).

## Cut list (in this order)
1. SDK alert trigger → paste the alert into the chat UI
2. Postmortem issue → agent writes it in chat
3. `restart_service` tool
4. **Never cut:** the sandbox proof, the approval pause, the refresh, the video

# TrueForge Challenge 

## Agent Harness Hackathon

STARTER GUIDE: Follow the [TrueForge.dev quickstart](https://trueforge.dev/quickstart). Run TrueForge locally to start your agent harness build. 

CHALLENGE: Build an agent on TrueForge that finishes a real job. Chatbots answer questions. Agents do things: open a PR, query a database, run a script, roll something back. TrueForge is TrueFoundry's open-source agent harness. It sits between the model and everything the model touches.

Your agent has to run on TrueForge (chat UI, HTTP API, or TypeScript SDK). Judges need to see the harness at work: a real tool call, code running in a sandbox, or a pause before something irreversible. Any domain is fine. Pick one job and ship it.

What TrueForge already does for you (use one of these hard; better projects use more than one):

* Tools via MCP, including OAuth servers, plus built-in tools and web search  
* Sandbox execution for agent-written code  
* Human approval before sensitive actions  
* Subagents for pieces of the job  
* Sessions that survive refresh, reconnect, and restart  
* Any model provider (OpenAI, Anthropic, Gemini, DeepSeek, or OpenAI-compatible)  
* Skills: instruction packs the agent loads when a task needs them

Ideas if you're stuck:

* Approval-gated assistant: draft the email or ticket, then wait for you before sending. Reaches: Gmail or Slack  
* Analytics agent: plain-English question in, SQL out, result explained. Reaches: your database  
* Code review agent: read a PR, run tests in the sandbox, leave comments. Reaches: GitHub  
* Research desk: spawn subagents, pull sources, merge the answer. Reaches: web search  
* Incident responder: read-only investigation first, then ask before restart or rollback. Reaches: your cloud / observability tools  
* Untrusted code runner: someone else's code, isolated sandbox, result back safely. Reaches: the sandbox

Submission checklist:

* Agent runs on TrueForge and the harness is doing real work  
* Public repo with a README someone else can follow  
* No keys or personal data in the repo or the video  
* Demo of about three minutes. If you have an approval gate or sandbox step, show it

Tips for the week:

1. If your demo would work as a plain chat window, change the project.  
2. One finished job beats three half-built features.  
3. Film the pause. Judges score control and safety, and most teams forget to show it.  
4. Someone who is not you should be able to clone the repo and run it.

RESOURCES:

* Quickest start (no account, no clone): npx @truefoundry/trueforge  
* Full stack under Compose: git clone git@github.com:truefoundry/trueforge.git cd trueforge && docker compose up  
* Introduction: [https://trueforge.dev/introduction](https://trueforge.dev/introduction)  
* Quickstart: [https://trueforge.dev/quickstart](https://trueforge.dev/quickstart)  
* Initial setup (models, MCP, skills, sandbox): [https://trueforge.dev/harness/initial-setup](https://trueforge.dev/harness/initial-setup)  
* MCP servers: [https://trueforge.dev/mcp-servers](https://trueforge.dev/mcp-servers)  
* Sandbox: [https://trueforge.dev/sandbox](https://trueforge.dev/sandbox)  
* Create an agent: [https://trueforge.dev/create-agent/overview](https://trueforge.dev/create-agent/overview)  
* Harness capabilities: [https://trueforge.dev/key-features/overview](https://trueforge.dev/key-features/overview)  
* SDK: [https://trueforge.dev/api/overview](https://trueforge.dev/api/overview)  
* GitHub: [https://github.com/truefoundry/trueforge](https://github.com/truefoundry/trueforge)  
* Hackathon page: [https://www.wemakedevs.org/hackathons/trueforge](https://www.wemakedevs.org/hackathons/trueforge)

Bring your own model API key. TrueForge works with any provider. Online folks use their own keys. SF in-person may get OpenAI credits if the event is offering them.

CONTACT INFO:

* WeMakeDevs Discord during the event, or GitHub issues on [https://github.com/truefoundry/trueforge](https://github.com/truefoundry/trueforge)  
* \[Add named contact / DevRel here\]

GIVEAWAYS:

* Best Use of TrueForge: most out of the harness (MCP, sandbox, approvals, subagents, durable sessions)  
* Interviews at TrueFoundry for the strongest projects  
* Certificate of participation for every valid submission  
* \[Add event-specific hardware / swag prizes here\]


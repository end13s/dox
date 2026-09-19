/**
 * Stretch: polls the demo service's /metrics endpoint, and when the error
 * rate crosses a threshold, starts a new TrueForge session on the
 * oncall-forge agent with the alert text — no human types anything.
 *
 * Cut first if it isn't working by ~3:15 (see oncall-forge-schedule.md
 * cut list) — the fallback is pasting the alert into the chat UI by hand.
 */

import { TrueForgeClient } from "@truefoundry/trueforge-sdk";

const DEMO_METRICS_URL = process.env.DEMO_METRICS_URL ?? "http://localhost:8000/metrics";
const ERROR_RATE_THRESHOLD = 0.05;
const POLL_INTERVAL_MS = 5000;
const AGENT_NAME = "oncall-forge";

const client = new TrueForgeClient();

let alertFired = false;

async function pollOnce(): Promise<void> {
  const res = await fetch(DEMO_METRICS_URL);
  const metrics = (await res.json()) as { error_rate: number; requests: number; errors: number };

  if (metrics.error_rate > ERROR_RATE_THRESHOLD && !alertFired) {
    alertFired = true;
    const alertText =
      `ALERT: checkout-service-demo error rate is ${(metrics.error_rate * 100).toFixed(1)}% ` +
      `(${metrics.errors}/${metrics.requests} requests failing). Investigate and remediate.`;

    await client.sessions.create({
      agent: AGENT_NAME,
      message: alertText,
    });

    console.log("Alert fired, session created:", alertText);
  }

  if (metrics.error_rate <= ERROR_RATE_THRESHOLD) {
    alertFired = false;
  }
}

setInterval(() => {
  pollOnce().catch((err) => console.error("poll failed:", err));
}, POLL_INTERVAL_MS);

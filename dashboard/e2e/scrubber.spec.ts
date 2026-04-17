import { expect, test } from "@playwright/test";

/**
 * Slice 29d — share page scrubber replays a completed run.
 *
 * Stubs the backend JSON endpoint so this spec can run without a live
 * FastAPI service. Asserts the scrubber renders, drag-to-0 rewinds the
 * graph (no aria-current on any node), drag-to-max restores the final
 * state, and Space auto-advances playback.
 */

const WORKFLOW = {
  name: "research_report",
  description: "Research a topic and produce a validated report",
  process: "sequential",
  agent_roles: ["researcher", "analyst", "writer", "validator"],
  task_names: ["research", "analysis", "writing", "validation"],
  parallel_tasks: null,
  inputs_schema: { topic: "str" },
  manager_agent: null,
};

const now = new Date();
const ts = (offsetMs: number) =>
  new Date(now.getTime() + offsetMs).toISOString();

const SHARE_PAYLOAD = {
  task_id: "shared-run-1",
  topic: "AI in retail 2026",
  domain: "finance",
  workflow: "research_report",
  status: "completed",
  duration_seconds: 4.5,
  result: "Final report body.",
  events: [
    {
      task_id: "shared-run-1",
      agent_role: "researcher",
      state: "active",
      detail: "starting",
      ts: ts(0),
    },
    {
      task_id: "shared-run-1",
      agent_role: "researcher",
      state: "completed",
      detail: "done",
      ts: ts(800),
    },
    {
      task_id: "shared-run-1",
      agent_role: "analyst",
      state: "active",
      detail: "analyzing",
      ts: ts(1_000),
    },
    {
      task_id: "shared-run-1",
      agent_role: "analyst",
      state: "completed",
      detail: "done",
      ts: ts(1_500),
    },
  ],
};

test.describe("Share page scrubber", () => {
  test.beforeEach(async ({ page }) => {
    // Only intercept the BACKEND share endpoint. Using a predicate lets us
    // match the full URL (query string included) and skip the Next.js page
    // request at localhost:3099/share/... which shares the /share/ segment.
    await page.route(
      (url) => url.port === "8060" && url.pathname.startsWith("/share/"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(SHARE_PAYLOAD),
        });
      },
    );
    await page.route("**/workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([WORKFLOW]),
      });
    });
    // GraphPane on the share page still kicks off an SSE subscription in
    // RunView's kanban branch — but ShareRunView bypasses that entirely.
    // Still, defensively stub the events endpoint so nothing stalls.
    await page.route("**/crew/run/*/events", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: "retry: 10000\n\n",
      });
    });
  });

  test("renders scrubber and auto-advances with Space", async ({ page }) => {
    await page.goto("/share/demo-token");

    const scrubber = page.getByTestId("scrubber");
    await expect(scrubber).toBeVisible();

    // At max index: last event was analyst completed, so no live nodes.
    const slider = page.getByRole("slider", { name: /scrub run/i });
    await expect(slider).toHaveAttribute(
      "aria-valuenow",
      String(SHARE_PAYLOAD.events.length),
    );
    await expect(page.locator("[aria-current='true']")).toHaveCount(0);

    // Drag to 0: no events applied, so no live nodes and no firing edges.
    await slider.fill("0");
    await expect(page.locator("[aria-current='true']")).toHaveCount(0);
    await expect(
      page.locator("[data-edge-state='firing'], [data-edge-state='packet']"),
    ).toHaveCount(0);

    // Drag to index 3 (researcher completed + analyst active): analyst lit.
    await slider.fill("3");
    await expect(page.getByTestId("agent-node-analyst")).toHaveAttribute(
      "aria-current",
      "true",
    );

    // Space on the scrubber starts playback — wait for the Pause button.
    await scrubber.focus();
    await page.keyboard.press("Space");
    await expect(
      page.getByRole("button", { name: /pause/i }),
    ).toBeVisible();
  });

  test("expired / invalid tokens render status cards, not the scrubber", async ({
    page,
  }) => {
    const backendShare = (url: URL) =>
      url.port === "8060" && url.pathname.startsWith("/share/");
    await page.unroute(backendShare);
    await page.route(backendShare, async (route) => {
      await route.fulfill({ status: 410, body: "gone" });
    });
    await page.goto("/share/expired-token");
    await expect(page.getByRole("heading", { name: /expired/i })).toBeVisible();
    await expect(page.getByTestId("scrubber")).toHaveCount(0);
  });
});

import { expect, test } from "@playwright/test";

/**
 * Slice 29a — graph topology renders the correct node + edge count for a
 * research_report sequential workflow.
 *
 * The test stubs the backend (/workflows + SSE stream) so it can run without
 * the FastAPI service. Slice 29b will extend this spec with live animation
 * assertions (edge-state=firing, aria-current on exactly one node).
 */

const RESEARCH_REPORT_WORKFLOW = {
  name: "research_report",
  description: "Research a topic and produce a validated report",
  process: "sequential",
  agent_roles: ["researcher", "analyst", "writer", "validator"],
  task_names: ["research", "analysis", "writing", "validation"],
  parallel_tasks: null,
  inputs_schema: { topic: "str" },
  manager_agent: null,
};

test.describe("Graph view — slice 29a topology", () => {
  test("renders 4 agent nodes and 3 edges for research_report", async ({
    page,
  }) => {
    await page.route("**/workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([RESEARCH_REPORT_WORKFLOW]),
      });
    });

    // Minimal SSE stream — no agent_state events; we're asserting topology, not
    // live state. The RunView will stay in "queued" for every node.
    await page.route("**/crew/run/*/events", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: "retry: 10000\n\n",
      });
    });

    await page.goto("/runs/test-graph-topology");

    await expect(page.getByTestId("graph-pane")).toBeVisible();

    for (const role of RESEARCH_REPORT_WORKFLOW.agent_roles) {
      await expect(page.getByTestId(`agent-node-${role}`)).toBeVisible();
    }

    // React Flow tags every rendered edge with class `react-flow__edge`.
    // A sequential 4-agent workflow yields 3 edges.
    await expect(page.locator(".react-flow__edge")).toHaveCount(3);
  });

  test("animates the active node (aria-current) and firing edge (data-edge-state)", async ({
    page,
  }) => {
    await page.route("**/workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([RESEARCH_REPORT_WORKFLOW]),
      });
    });

    // SSE stream fires one event per ~100ms so the test sees the live
    // transition: researcher completes → analyst activates. The edge
    // between them should flip to firing/packet.
    const now = new Date().toISOString();
    const sse = [
      `event: agent_state\ndata: ${JSON.stringify({ task_id: "t", agent_role: "researcher", state: "active", detail: "", ts: now })}\n\n`,
      `event: agent_state\ndata: ${JSON.stringify({ task_id: "t", agent_role: "researcher", state: "completed", detail: "", ts: now })}\n\n`,
      `event: agent_state\ndata: ${JSON.stringify({ task_id: "t", agent_role: "analyst", state: "active", detail: "", ts: now })}\n\n`,
    ].join("");

    await page.route("**/crew/run/*/events", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: sse,
      });
    });

    await page.goto("/runs/test-live-animation");

    // Analyst has just activated and should carry aria-current.
    await expect(page.getByTestId("agent-node-analyst")).toHaveAttribute(
      "aria-current",
      "true",
      { timeout: 10_000 },
    );
    // Exactly one node is "live" at a time.
    await expect(page.locator("[aria-current='true']")).toHaveCount(1);

    // At least one edge lights up with firing/packet state.
    await expect(
      page.locator("[data-edge-state='firing'], [data-edge-state='packet']"),
    ).not.toHaveCount(0);
  });

  test("view toggle switches between graph and kanban board", async ({
    page,
  }) => {
    await page.route("**/workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([RESEARCH_REPORT_WORKFLOW]),
      });
    });
    await page.route("**/crew/run/*/events", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: "retry: 10000\n\n",
      });
    });

    await page.goto("/runs/test-toggle");

    await expect(page.getByTestId("graph-pane")).toBeVisible();
    await expect(page.getByTestId("board-pane")).toHaveCount(0);

    await page.getByRole("button", { name: /board/i }).click();

    await expect(page.getByTestId("board-pane")).toBeVisible();
    await expect(page.getByTestId("graph-pane")).toHaveCount(0);
  });
});

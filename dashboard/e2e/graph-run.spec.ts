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

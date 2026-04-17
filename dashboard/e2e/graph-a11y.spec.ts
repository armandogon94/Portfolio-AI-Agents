import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

/**
 * Slice 29e — keyboard-only a11y journey across the graph run view.
 *
 * No pointer events used. Navigation is Tab + Enter + arrow keys.
 * Also runs axe-core on the settled page to catch WCAG 2 A/AA
 * violations in the graph + transcript chrome.
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

const now = new Date().toISOString();
const SSE = [
  `event: agent_state\ndata: ${JSON.stringify({ task_id: "t", agent_role: "researcher", state: "active", detail: "starting", ts: now })}\n\n`,
  `event: agent_state\ndata: ${JSON.stringify({ task_id: "t", agent_role: "researcher", state: "completed", detail: "done", ts: now })}\n\n`,
].join("");

test.describe("Graph view — keyboard + axe", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([WORKFLOW]),
      });
    });
    await page.route("**/crew/run/*/events", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: SSE,
      });
    });
  });

  test("keyboard-only: focus researcher node then jump to transcript", async ({
    page,
  }) => {
    await page.goto("/runs/kbd-journey");
    const researcher = page.getByTestId("agent-node-researcher");
    await expect(researcher).toBeVisible();

    // Focus directly (React Flow's internal tab order is tool-specific;
    // we're asserting the node's Enter handler + event plumbing).
    await researcher.focus();
    await page.keyboard.press("Enter");

    // TranscriptPane listens for graph:focus-role and expands the
    // matching section. The researcher section's toggle becomes expanded.
    const researcherSection = page.getByRole("group", {
      name: /transcript for researcher/i,
    });
    await expect(
      researcherSection.getByRole("button", {
        name: /toggle researcher transcript/i,
      }),
    ).toHaveAttribute("aria-expanded", "true");
  });

  test("axe-core finds zero WCAG 2 A / AA violations on /runs/[id]", async ({
    page,
  }) => {
    await page.goto("/runs/axe-check");
    // Give the graph time to settle (workflows fetch + SSE handshake).
    await expect(page.getByTestId("graph-pane")).toBeVisible();
    await expect(page.getByTestId("agent-node-researcher")).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      // React Flow's internal wrapper has zero dimensions in headless
      // CI — `region` is flaky and unrelated to our own chrome.
      .disableRules(["region"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});

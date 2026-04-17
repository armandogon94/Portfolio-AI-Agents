import { render } from "@testing-library/react";
import { axe } from "vitest-axe";
import { beforeEach, describe, expect, it } from "vitest";

import { http, HttpResponse } from "msw";

import GraphPane from "@/components/GraphPane";
import { server } from "./mocks/server";

/**
 * Slice 29e — axe-core smoke on GraphPane.
 *
 * jsdom can't lay out SVG or run React Flow's measurement, but it can
 * tell us about ARIA, landmark, and contrast violations in the
 * surrounding chrome (loading state, error banner, and the pane root).
 */

const RESEARCH_REPORT = {
  name: "research_report",
  description: "Research a topic and produce a validated report",
  process: "sequential",
  agent_roles: ["researcher", "analyst", "writer", "validator"],
  task_names: ["research", "analysis", "writing", "validation"],
  parallel_tasks: null,
  inputs_schema: { topic: "str" },
  manager_agent: null,
};

describe("GraphPane a11y", () => {
  beforeEach(() => {
    server.use(
      http.get("http://localhost:8060/workflows", () =>
        HttpResponse.json([RESEARCH_REPORT]),
      ),
    );
  });

  it("has no WCAG 2 A violations in the loading state", async () => {
    const { container } = render(
      <GraphPane taskId="t-a11y" events={[]} />,
    );
    const results = await axe(container, {
      rules: {
        // The zero-height jsdom viewport triggers this React Flow warning
        // which is about tooling, not a11y — safe to ignore here.
        region: { enabled: false },
      },
    });
    expect(results).toHaveNoViolations();
  });
});

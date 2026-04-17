/**
 * Topology tests for buildGraph + dagreLayout (slice-29a, DEC-30).
 *
 * Each workflow in the registry must produce a correct graph
 * (nodes, edges, layout) purely from metadata.
 */

import { describe, expect, it } from "vitest";

import type { WorkflowInfo } from "@/lib/types";

const baseSequential: WorkflowInfo = {
  name: "research_report",
  description: "test",
  process: "sequential",
  agent_roles: ["researcher", "analyst", "writer", "validator"],
  task_names: ["research", "analysis", "writing", "validation"],
  parallel_tasks: null,
  inputs_schema: {},
};

const baseParallel: WorkflowInfo = {
  name: "meeting_prep",
  description: "test",
  process: "sequential",
  agent_roles: [
    "attendee_researcher",
    "topic_researcher",
    "agenda_writer",
    "talking_points_writer",
  ],
  task_names: [
    "attendee_research",
    "topic_research",
    "build_agenda",
    "build_talking_points",
  ],
  parallel_tasks: [["attendee_research", "topic_research"]],
  inputs_schema: {},
};

const baseHierarchical: WorkflowInfo = {
  name: "support_triage",
  description: "test",
  process: "hierarchical",
  agent_roles: [
    "triage_manager",
    "kb_searcher",
    "sentiment_analyst",
    "response_writer",
  ],
  task_names: ["triage_route", "kb_search", "sentiment_analyze", "response_draft"],
  parallel_tasks: null,
  inputs_schema: {},
  manager_agent: "triage_manager",
};

describe("buildGraph — topology per process type", () => {
  it("sequential → N nodes, N-1 edges, ranks incrementing left-to-right", async () => {
    const { buildGraph } = await import("@/lib/graph");
    const { nodes, edges } = buildGraph(baseSequential);

    expect(nodes).toHaveLength(4);
    expect(edges).toHaveLength(3);

    const ids = nodes.map((n) => n.id);
    expect(ids).toEqual([
      "researcher",
      "analyst",
      "writer",
      "validator",
    ]);

    expect(edges.map((e) => [e.source, e.target])).toEqual([
      ["researcher", "analyst"],
      ["analyst", "writer"],
      ["writer", "validator"],
    ]);
  });

  it("sequential + parallel → fan-out + fan-in edges at the right ranks", async () => {
    const { buildGraph } = await import("@/lib/graph");
    const { nodes, edges } = buildGraph(baseParallel);

    expect(nodes).toHaveLength(4);
    // attendee_researcher → agenda_writer, topic_researcher → agenda_writer,
    // agenda_writer → talking_points_writer
    const edgePairs = edges.map((e) => [e.source, e.target]);
    expect(edgePairs).toContainEqual([
      "attendee_researcher",
      "agenda_writer",
    ]);
    expect(edgePairs).toContainEqual(["topic_researcher", "agenda_writer"]);
    expect(edgePairs).toContainEqual([
      "agenda_writer",
      "talking_points_writer",
    ]);
    expect(edges).toHaveLength(3);
  });

  it("hierarchical → manager at rank 0, specialists at rank 1, delegation edges", async () => {
    const { buildGraph } = await import("@/lib/graph");
    const { nodes, edges } = buildGraph(baseHierarchical);

    expect(nodes).toHaveLength(4);
    const manager = nodes.find((n) => n.id === "triage_manager");
    expect(manager).toBeDefined();
    expect(manager?.data.kind).toBe("manager");

    const specialistEdges = edges.filter(
      (e) => e.source === "triage_manager",
    );
    expect(specialistEdges.map((e) => e.target).sort()).toEqual([
      "kb_searcher",
      "response_writer",
      "sentiment_analyst",
    ]);
  });

  it("sequential + parallel (meeting_prep) — mixed topology holds", async () => {
    const { buildGraph } = await import("@/lib/graph");
    const { nodes, edges } = buildGraph(baseParallel);

    // attendee + topic researcher should share rank 0; agenda_writer at
    // rank 1; talking_points_writer at rank 2.
    const rankByRole = new Map(nodes.map((n) => [n.id, n.data.rank]));
    expect(rankByRole.get("attendee_researcher")).toBe(0);
    expect(rankByRole.get("topic_researcher")).toBe(0);
    expect(rankByRole.get("agenda_writer")).toBe(1);
    expect(rankByRole.get("talking_points_writer")).toBe(2);
  });

  it("unknown process throws UnknownProcessError", async () => {
    const { buildGraph, UnknownProcessError } = await import("@/lib/graph");
    const bad = { ...baseSequential, process: "octopus" as unknown as "sequential" };
    expect(() => buildGraph(bad)).toThrow(UnknownProcessError);
  });

  it("empty task_names produces an empty graph without crashing", async () => {
    const { buildGraph } = await import("@/lib/graph");
    const empty: WorkflowInfo = {
      ...baseSequential,
      agent_roles: [],
      task_names: [],
    };
    const { nodes, edges } = buildGraph(empty);
    expect(nodes).toEqual([]);
    expect(edges).toEqual([]);
  });

  it("dagre layout assigns distinct x/y to every node (no overlap)", async () => {
    const { buildGraph } = await import("@/lib/graph");
    const { layoutNodes } = await import("@/lib/dagreLayout");
    const { nodes, edges } = buildGraph(baseSequential);
    const positioned = layoutNodes(nodes, edges, "LR");

    const positions = positioned.map((n) => `${n.position.x},${n.position.y}`);
    const unique = new Set(positions);
    expect(unique.size).toBe(nodes.length);
  });
});

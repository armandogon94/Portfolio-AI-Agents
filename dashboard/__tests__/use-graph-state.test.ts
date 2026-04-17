import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useGraphState } from "@/lib/useGraphState";
import type { AgentStateEvent, WorkflowInfo } from "@/lib/types";

const RESEARCH_REPORT: WorkflowInfo = {
  name: "research_report",
  description: "Sequential research pipeline",
  process: "sequential",
  agent_roles: ["researcher", "analyst", "writer", "validator"],
  task_names: ["research", "analysis", "writing", "validation"],
  parallel_tasks: null,
  inputs_schema: { topic: "str" },
  manager_agent: null,
};

function ev(
  role: string,
  state: AgentStateEvent["state"],
  at: number,
  detail = "",
): AgentStateEvent {
  return {
    task_id: "t-1",
    agent_role: role,
    state,
    detail,
    ts: new Date(at).toISOString(),
  };
}

describe("useGraphState reducer", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("applies last-wins state per agent role", () => {
    const events: AgentStateEvent[] = [
      ev("researcher", "queued", 1_000),
      ev("researcher", "active", 2_000),
      ev("researcher", "completed", 3_000),
      ev("analyst", "active", 3_100),
    ];
    const { result } = renderHook(() =>
      useGraphState(events, RESEARCH_REPORT),
    );

    expect(result.current.nodeStates.researcher).toBe("completed");
    expect(result.current.nodeStates.analyst).toBe("active");
    // Untouched roles default to "queued" (the AgentNode idle visual).
    expect(result.current.nodeStates.writer).toBe("queued");
    expect(result.current.nodeStates.validator).toBe("queued");
  });

  it("keeps waiting_on_tool distinct from waiting_on_agent", () => {
    const { result } = renderHook(() =>
      useGraphState(
        [
          ev("researcher", "waiting_on_tool", 1_000, "web_search"),
          ev("analyst", "waiting_on_agent", 1_100, "blocked on researcher"),
        ],
        RESEARCH_REPORT,
      ),
    );
    expect(result.current.nodeStates.researcher).toBe("waiting_on_tool");
    expect(result.current.nodeStates.analyst).toBe("waiting_on_agent");
  });

  it("sets lastTransition when a downstream node becomes active", () => {
    const now = Date.now();
    const events: AgentStateEvent[] = [
      ev("researcher", "completed", now - 200),
      ev("analyst", "active", now - 100),
    ];
    const { result } = renderHook(() =>
      useGraphState(events, RESEARCH_REPORT),
    );
    expect(result.current.lastTransition).toEqual({
      from: "researcher",
      to: "analyst",
      ts: events[1].ts,
    });
    // Within the 3s firing window, the edge is firing (or its sub-state
    // packet within the first 600ms).
    const state = result.current.edgeStates["researcher->analyst"];
    expect(["firing", "packet"]).toContain(state);
  });

  it("transition clears after 3 seconds (fake timers)", () => {
    const base = Date.now();
    vi.useFakeTimers();
    vi.setSystemTime(new Date(base + 700));
    const events: AgentStateEvent[] = [
      ev("researcher", "completed", base),
      ev("analyst", "active", base + 50),
    ];
    const { result, rerender } = renderHook(() =>
      useGraphState(events, RESEARCH_REPORT),
    );
    // Age = 650ms → past the 600ms packet window, still inside firing.
    expect(result.current.edgeStates["researcher->analyst"]).toBe("firing");

    act(() => {
      vi.setSystemTime(new Date(base + 4_000));
      vi.advanceTimersByTime(4_000);
    });
    rerender();

    expect(result.current.edgeStates["researcher->analyst"]).not.toBe(
      "firing",
    );
    expect(result.current.edgeStates["researcher->analyst"]).not.toBe(
      "packet",
    );
  });

  it("no events → every node queued and every edge idle", () => {
    const { result } = renderHook(() => useGraphState([], RESEARCH_REPORT));
    expect(Object.values(result.current.nodeStates)).toEqual([
      "queued",
      "queued",
      "queued",
      "queued",
    ]);
    expect(result.current.edgeStates["researcher->analyst"]).toBe("idle");
    expect(result.current.edgeStates["analyst->writer"]).toBe("idle");
    expect(result.current.edgeStates["writer->validator"]).toBe("idle");
    expect(result.current.lastTransition).toBeNull();
  });

  it("skips the decay heartbeat under prefers-reduced-motion but still derives state", () => {
    const setInterval = vi.spyOn(globalThis, "setInterval");
    const reducedMotion = vi.fn<(query: string) => MediaQueryList>(
      (query: string) => ({
        matches: query.includes("reduce"),
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }) as unknown as MediaQueryList,
    );
    const originalMatchMedia = window.matchMedia;
    window.matchMedia = reducedMotion as unknown as typeof window.matchMedia;
    try {
      const { result } = renderHook(() =>
        useGraphState(
          [
            ev("researcher", "completed", Date.now() - 200),
            ev("analyst", "active", Date.now() - 100),
          ],
          RESEARCH_REPORT,
        ),
      );
      // State still applies — the reducer is pure.
      expect(result.current.nodeStates.analyst).toBe("active");
      // But no animation heartbeat kicked in.
      expect(setInterval).not.toHaveBeenCalled();
    } finally {
      window.matchMedia = originalMatchMedia;
      setInterval.mockRestore();
    }
  });

  it("failed event sets node to failed and blocks downstream firing", () => {
    const events: AgentStateEvent[] = [
      ev("researcher", "active", 1_000),
      ev("researcher", "failed", 1_500, "boom"),
    ];
    const { result } = renderHook(() =>
      useGraphState(events, RESEARCH_REPORT),
    );
    expect(result.current.nodeStates.researcher).toBe("failed");
    // Downstream edge must NOT be firing/packet when its source has failed.
    const edge = result.current.edgeStates["researcher->analyst"];
    expect(edge).not.toBe("firing");
    expect(edge).not.toBe("packet");
  });
});

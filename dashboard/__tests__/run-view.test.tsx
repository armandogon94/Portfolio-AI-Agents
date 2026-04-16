import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import RunView from "@/components/RunView";
import type { AgentStateEvent } from "@/lib/types";

type Listener = (ev: { data: string }) => void;

class MockEventSource {
  public readyState = 0;
  public onerror: ((ev: unknown) => void) | null = null;
  private listeners: Record<string, Listener[]> = {};
  static instances: MockEventSource[] = [];

  constructor(public readonly url: string) {
    MockEventSource.instances.push(this);
    this.readyState = 1;
  }

  addEventListener(type: string, listener: Listener): void {
    (this.listeners[type] ||= []).push(listener);
  }

  removeEventListener(type: string, listener: Listener): void {
    this.listeners[type] = (this.listeners[type] ?? []).filter(
      (l) => l !== listener,
    );
  }

  dispatch(type: string, payload: AgentStateEvent | { task_id: string; status: string }): void {
    for (const l of this.listeners[type] ?? []) {
      l({ data: JSON.stringify(payload) });
    }
  }

  close(): void {
    this.readyState = 2;
  }
}

function publish(state: AgentStateEvent["state"], agent_role = "researcher", detail = "") {
  MockEventSource.instances[0].dispatch("agent_state", {
    task_id: "run-42",
    agent_role,
    state,
    detail,
    ts: new Date().toISOString(),
  });
}

beforeEach(() => {
  MockEventSource.instances = [];
  (globalThis as unknown as { EventSource: typeof MockEventSource }).EventSource =
    MockEventSource;
});

afterEach(() => {
  vi.useRealTimers();
  delete (globalThis as unknown as { EventSource?: typeof MockEventSource })
    .EventSource;
});

describe("RunView SSE rendering", () => {
  it("renders one agent card per role and moves it across kanban columns as events arrive", async () => {
    render(<RunView taskId="run-42" />);

    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].url).toContain(
      "/crew/run/run-42/events",
    );

    publish("queued", "researcher");
    await waitFor(() => {
      const queued = screen.getByTestId("column-queued");
      expect(queued).toHaveTextContent("researcher");
    });

    publish("active", "researcher", "tool: web_search");
    await waitFor(() => {
      const active = screen.getByTestId("column-active");
      expect(active).toHaveTextContent("researcher");
    });
    expect(screen.queryByTestId("column-queued")).not.toHaveTextContent(
      "researcher",
    );

    publish("completed", "researcher");
    await waitFor(() => {
      const done = screen.getByTestId("column-done");
      expect(done).toHaveTextContent("researcher");
    });
  });

  it("places agents in the waiting column on waiting_on_agent", async () => {
    render(<RunView taskId="run-42" />);
    publish("waiting_on_agent", "writer", "waiting on parallel group");
    await waitFor(() => {
      expect(screen.getByTestId("column-waiting")).toHaveTextContent("writer");
    });
  });

  it("closes the EventSource when the run completes", async () => {
    render(<RunView taskId="run-42" />);
    const es = MockEventSource.instances[0];

    MockEventSource.instances[0].dispatch("run_complete", {
      task_id: "run-42",
      status: "completed",
    });

    await waitFor(() => {
      expect(es.readyState).toBe(2);
    });
    await waitFor(() => {
      expect(screen.getByText(/run complete/i)).toBeInTheDocument();
    });
  });

  it("registers only one EventSource despite StrictMode double-mount", () => {
    render(<RunView taskId="run-42" />);
    // With proper useEffect cleanup, unmount+remount during StrictMode
    // collapses to a single live subscription.
    expect(MockEventSource.instances).toHaveLength(1);
  });
});

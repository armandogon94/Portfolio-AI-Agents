"use client";

import { useEffect, useState } from "react";

import type { AgentRunState, AgentStateEvent } from "./types";

export interface RunStreamState {
  events: AgentStateEvent[];
  completed: boolean;
  status?: "completed" | "failed";
  error: string | null;
}

/**
 * Subscribe to a crew run's SSE stream (slice-19 contract).
 *
 * Uses native EventSource. `useEffect` cleanup + a `disposed` guard make
 * React 19 StrictMode double-mount collapse to a single live subscription.
 */
export function useAgentEvents(
  taskId: string,
  apiUrl: string = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060",
): RunStreamState {
  const [state, setState] = useState<RunStreamState>({
    events: [],
    completed: false,
    error: null,
  });

  useEffect(() => {
    let disposed = false;
    const es = new EventSource(`${apiUrl}/crew/run/${taskId}/events`);

    const handleAgentState = (event: MessageEvent) => {
      if (disposed) return;
      try {
        const payload = JSON.parse(event.data) as AgentStateEvent;
        setState((prev) => ({ ...prev, events: [...prev.events, payload] }));
      } catch (err) {
        // ignore malformed frames
        console.warn("sse: malformed agent_state frame", err);
      }
    };

    const handleRunComplete = (event: MessageEvent) => {
      if (disposed) return;
      try {
        const payload = JSON.parse(event.data) as {
          status: "completed" | "failed";
        };
        setState((prev) => ({ ...prev, completed: true, status: payload.status }));
      } catch {
        setState((prev) => ({ ...prev, completed: true }));
      }
      es.close();
    };

    const handleError = () => {
      if (disposed) return;
      setState((prev) => ({
        ...prev,
        error: "Connection interrupted — retrying…",
      }));
    };

    es.addEventListener("agent_state", handleAgentState as EventListener);
    es.addEventListener("run_complete", handleRunComplete as EventListener);
    es.addEventListener("error", handleError as EventListener);

    return () => {
      disposed = true;
      es.removeEventListener("agent_state", handleAgentState as EventListener);
      es.removeEventListener("run_complete", handleRunComplete as EventListener);
      es.removeEventListener("error", handleError as EventListener);
      es.close();
    };
  }, [taskId, apiUrl]);

  return state;
}

export const TERMINAL_STATES: AgentRunState[] = ["completed", "failed"];

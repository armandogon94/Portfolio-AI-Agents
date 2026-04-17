/**
 * Derive live graph state from the SSE event stream (slice-29b).
 *
 * Pure reducer. Takes the full `events` array + the workflow topology and
 * returns:
 *   - nodeStates: latest AgentRunState per agent_role (defaults to "queued")
 *   - edgeStates: derived per-edge state (idle | armed | firing | packet | completed)
 *   - lastTransition: the most recent source→target handoff (null if none)
 *
 * The same hook serves the live run view and the share-page scrubber — the
 * scrubber just slices `events` before passing them in.
 *
 * Time-windowed states (firing, packet) re-evaluate on a clock tick: the
 * hook re-derives every 250ms while any transition is within its window so
 * the UI can drop out of "firing" back to "completed" without waiting for
 * the next SSE event.
 */

import { useEffect, useMemo, useState } from "react";

import { buildGraph } from "./graph";
import type {
  AgentRunState,
  AgentStateEvent,
  WorkflowInfo,
} from "./types";

export type EdgeAnimatedState =
  | "idle"
  | "armed"
  | "firing"
  | "packet"
  | "completed";

export interface GraphTransition {
  from: string;
  to: string;
  ts: string;
}

export interface GraphState {
  nodeStates: Record<string, AgentRunState>;
  edgeStates: Record<string, EdgeAnimatedState>;
  lastTransition: GraphTransition | null;
}

const FIRING_WINDOW_MS = 3_000;
const PACKET_WINDOW_MS = 600;
const TERMINAL_STATES = new Set<AgentRunState>(["completed", "failed"]);

export function useGraphState(
  events: AgentStateEvent[],
  workflow: WorkflowInfo | null,
): GraphState {
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    if (!events.length) return;
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, [events.length]);

  return useMemo(() => {
    if (!workflow) {
      return { nodeStates: {}, edgeStates: {}, lastTransition: null };
    }
    const { nodes, edges } = buildGraph(workflow);

    const nodeStates: Record<string, AgentRunState> = {};
    for (const n of nodes) nodeStates[n.id] = "queued";

    let lastTransition: GraphTransition | null = null;
    for (const event of events) {
      const role = event.agent_role;
      if (!role || role === "crew") continue;
      const previous = nodeStates[role];
      nodeStates[role] = event.state;
      if (event.state === "active" && previous !== "active") {
        // A node just became active — find the most recent completed node
        // that isn't this one; that's the transition source. Prefer edges
        // declared in the workflow topology.
        const upstream = edges.find(
          (e) => e.target === role && nodeStates[e.source] === "completed",
        );
        if (upstream) {
          lastTransition = {
            from: upstream.source,
            to: role,
            ts: event.ts,
          };
        }
      }
    }

    const transitionAge = lastTransition
      ? now - Date.parse(lastTransition.ts)
      : Number.POSITIVE_INFINITY;

    const edgeStates: Record<string, EdgeAnimatedState> = {};
    for (const edge of edges) {
      const src = nodeStates[edge.source] ?? "queued";
      const tgt = nodeStates[edge.target] ?? "queued";
      edgeStates[edge.id] = deriveEdgeState({
        src,
        tgt,
        isTransition:
          lastTransition?.from === edge.source &&
          lastTransition?.to === edge.target,
        transitionAge,
      });
    }

    return { nodeStates, edgeStates, lastTransition };
  }, [events, workflow, now]);
}

function deriveEdgeState(input: {
  src: AgentRunState;
  tgt: AgentRunState;
  isTransition: boolean;
  transitionAge: number;
}): EdgeAnimatedState {
  const { src, tgt, isTransition, transitionAge } = input;
  // A failed source never fires or packets downstream.
  if (src === "failed") {
    return TERMINAL_STATES.has(tgt) ? "completed" : "idle";
  }
  if (isTransition && transitionAge <= PACKET_WINDOW_MS) return "packet";
  if (
    isTransition &&
    transitionAge <= FIRING_WINDOW_MS &&
    src === "completed" &&
    (tgt === "active" ||
      tgt === "waiting_on_tool" ||
      tgt === "waiting_on_agent")
  ) {
    return "firing";
  }
  if (src === "completed" && tgt === "active") {
    // Within window but not the latest transition — still visually armed.
    return "armed";
  }
  if (
    (src === "active" ||
      src === "waiting_on_tool" ||
      src === "waiting_on_agent") &&
    tgt === "queued"
  ) {
    return "armed";
  }
  if (TERMINAL_STATES.has(src) && TERMINAL_STATES.has(tgt)) return "completed";
  return "idle";
}

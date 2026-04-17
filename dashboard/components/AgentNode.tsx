"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";

import { AgentIcon } from "@/components/AgentIcon";
import { StateChip } from "@/components/StateChip";
import type { AgentRunState } from "@/lib/types";

/**
 * React Flow custom node for a workflow agent.
 *
 * Slice-29a: idle-only visuals.
 * Slice-29b: state-driven halo + aria-current + failed shake.
 *   - active / waiting_on_tool / waiting_on_agent → pulsing halo
 *   - failed → rose border + one-shot shake
 *   - completed → indigo solid border
 *   - queued → slate border, dim
 * Animations are gated by prefers-reduced-motion (see globals.css).
 */

export interface AgentNodeData extends Record<string, unknown> {
  role: string;
  kind: "agent" | "manager" | "specialist";
  rank: number;
  state?: AgentRunState;
}

export type AgentNodeProps = NodeProps<{
  id: string;
  type: "agent";
  data: AgentNodeData;
  position: { x: number; y: number };
}>;

function prettyRole(role: string): string {
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const STATE_RING: Record<AgentRunState, string> = {
  queued:
    "border-zinc-200/80 dark:border-zinc-800",
  active:
    "border-indigo-400 ring-2 ring-indigo-300/60 dark:border-indigo-400 dark:ring-indigo-400/30",
  waiting_on_tool:
    "border-amber-400 ring-2 ring-amber-300/60 dark:border-amber-400 dark:ring-amber-400/30",
  waiting_on_agent:
    "border-amber-300 opacity-70 dark:border-amber-500/60",
  completed:
    "border-indigo-500 ring-1 ring-indigo-400/50 dark:border-indigo-400/80",
  failed:
    "border-rose-400 ring-2 ring-rose-300/50 dark:border-rose-500/70 dark:ring-rose-500/30",
};

function animationClass(state: AgentRunState): string {
  if (
    state === "active" ||
    state === "waiting_on_tool" ||
    state === "waiting_on_agent"
  ) {
    return "graph-node-active";
  }
  if (state === "failed") return "graph-node-failed";
  return "";
}

export function AgentNode({ data }: AgentNodeProps) {
  const state: AgentRunState = data.state ?? "queued";
  const isManager = data.kind === "manager";
  const isLive =
    state === "active" ||
    state === "waiting_on_tool" ||
    state === "waiting_on_agent";

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      // Emit a cross-pane event the TranscriptPane listens for — keeps
      // the graph/transcript coupling loose (no shared ref, no prop
      // drilling through RunView).
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("graph:focus-role", { detail: { role: data.role } }),
        );
      }
    }
  }

  return (
    <div
      data-testid={`agent-node-${data.role}`}
      data-node-state={state}
      role="button"
      tabIndex={0}
      aria-label={`Agent ${prettyRole(data.role)} — ${state}. Press Enter to jump to transcript.`}
      aria-current={isLive ? "true" : undefined}
      onKeyDown={handleKeyDown}
      className={[
        "min-w-[12rem] rounded-xl border bg-white p-3 shadow-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-indigo-500",
        "dark:bg-zinc-900/60",
        isManager && state === "queued"
          ? "border-indigo-300 ring-1 ring-indigo-200/50 dark:border-indigo-500/40 dark:ring-indigo-500/20"
          : STATE_RING[state],
        animationClass(state),
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span
            className={[
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ring-1",
              isManager
                ? "bg-gradient-to-br from-indigo-500 to-violet-600 text-white ring-indigo-300"
                : "bg-gradient-to-br from-indigo-500/15 to-violet-500/15 text-indigo-700 ring-indigo-200/60 dark:text-indigo-300 dark:ring-indigo-500/30",
            ].join(" ")}
          >
            <AgentIcon role={data.role} className="h-4 w-4" />
          </span>
          <span className="truncate text-sm font-semibold">
            {prettyRole(data.role)}
          </span>
        </div>
        <StateChip state={state} />
      </div>
      {isManager ? (
        <p className="mt-2 text-[11px] font-medium uppercase tracking-wider text-indigo-500">
          Manager
        </p>
      ) : null}
      <Handle type="source" position={Position.Right} className="!opacity-0" />
    </div>
  );
}

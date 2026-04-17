"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";

import { AgentIcon } from "@/components/AgentIcon";
import { StateChip } from "@/components/StateChip";
import type { AgentRunState } from "@/lib/types";

/**
 * React Flow custom node for a workflow agent (slice-29a).
 * State-driven halos land in slice-29b; for now the component renders
 * idle styling + an (optional) state chip sourced from props.
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

export function AgentNode({ data }: AgentNodeProps) {
  const state: AgentRunState = data.state ?? "queued";
  const isManager = data.kind === "manager";

  return (
    <div
      data-testid={`agent-node-${data.role}`}
      aria-label={`Agent ${prettyRole(data.role)} — ${state}`}
      className={[
        "min-w-[12rem] rounded-xl border bg-white p-3 shadow-sm transition-shadow",
        "dark:bg-zinc-900/60",
        isManager
          ? "border-indigo-300 ring-1 ring-indigo-200/50 dark:border-indigo-500/40 dark:ring-indigo-500/20"
          : "border-zinc-200/80 dark:border-zinc-800",
      ].join(" ")}
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

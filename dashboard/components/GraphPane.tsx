"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type EdgeTypes,
  type Node,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion } from "framer-motion";

import { AgentNode } from "@/components/AgentNode";
import { EdgeAnimated } from "@/components/EdgeAnimated";
import { apiClient } from "@/lib/api";
import { buildGraph } from "@/lib/graph";
import { layoutNodes } from "@/lib/dagreLayout";
import { useGraphState } from "@/lib/useGraphState";
import type { AgentStateEvent, WorkflowInfo } from "@/lib/types";

const MINIMAP_NODE_FILL: Record<string, string> = {
  queued: "#e4e4e7", // zinc-200
  active: "#a5b4fc", // indigo-300
  waiting_on_tool: "#fcd34d", // amber-300
  waiting_on_agent: "#fde68a", // amber-200
  completed: "#6366f1", // indigo-500
  failed: "#fb7185", // rose-400
};

export interface GraphPaneProps {
  taskId: string;
  workflowName?: string;
  events?: AgentStateEvent[];
}

const NODE_TYPES: NodeTypes = { agent: AgentNode as unknown as NodeTypes["agent"] };
const EDGE_TYPES: EdgeTypes = { animated: EdgeAnimated as unknown as EdgeTypes["animated"] };

export default function GraphPane(props: GraphPaneProps) {
  return (
    <ReactFlowProvider>
      <GraphPaneInner {...props} />
    </ReactFlowProvider>
  );
}

function GraphPaneInner({ workflowName, events = [] }: GraphPaneProps) {
  const [workflow, setWorkflow] = useState<WorkflowInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiClient
      .listWorkflows()
      .then((workflows) => {
        if (!active) return;
        const match =
          (workflowName && workflows.find((w) => w.name === workflowName)) ||
          workflows.find((w) => w.name === "research_report") ||
          workflows[0];
        setWorkflow(match ?? null);
      })
      .catch((err) => {
        if (!active) return;
        setError(err.message);
      });
    return () => {
      active = false;
    };
  }, [workflowName]);

  const { nodeStates, edgeStates } = useGraphState(events, workflow);

  const { nodes, edges } = useMemo(() => {
    if (!workflow) return { nodes: [] as Node[], edges: [] as Edge[] };
    const { nodes: rawNodes, edges: rawEdges } = buildGraph(workflow);
    const positioned = layoutNodes(rawNodes, rawEdges, "LR");
    const decorated: Node[] = positioned.map((n) => ({
      ...n,
      data: { ...n.data, state: nodeStates[n.id] ?? "queued" },
    }));
    const live: Edge[] = rawEdges.map((e) => ({
      ...e,
      data: { ...(e.data ?? {}), state: edgeStates[e.id] ?? "idle" },
    })) as Edge[];
    return { nodes: decorated, edges: live };
  }, [workflow, nodeStates, edgeStates]);

  if (error) {
    return (
      <p
        role="alert"
        className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300"
      >
        Graph unavailable: {error}
      </p>
    );
  }

  if (!workflow) {
    return (
      <p className="rounded-md border border-zinc-200 bg-white p-6 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
        Loading workflow…
      </p>
    );
  }

  return (
    <div
      data-testid="graph-pane"
      aria-label="Workflow graph"
      role="region"
      className="flex w-full flex-col overflow-hidden rounded-xl border border-zinc-200/80 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60"
    >
      <motion.header
        layoutId={`wf-${workflow.name}`}
        className="flex flex-wrap items-center gap-2 border-b border-zinc-100 bg-zinc-50/60 px-3 py-2 text-xs text-zinc-600 dark:border-zinc-800 dark:bg-zinc-800/30 dark:text-zinc-400"
      >
        <span className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
          {workflow.process}
        </span>
        <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
          {workflow.agent_roles.length} agents · {workflow.task_names.length} tasks
        </span>
        <span className="truncate">{workflow.description}</span>
      </motion.header>
      <div className="h-[28rem] w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          edgeTypes={EDGE_TYPES}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
        >
          <Background gap={20} size={1} className="bg-zinc-50/40 dark:bg-zinc-950/40" />
          <MiniMap
            pannable
            zoomable
            nodeColor={(n) =>
              MINIMAP_NODE_FILL[
                (n.data as { state?: string } | undefined)?.state ?? "queued"
              ] ?? MINIMAP_NODE_FILL.queued
            }
            nodeStrokeColor="#6366f1"
            className="!bg-white/80 dark:!bg-zinc-900/80"
          />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  );
}

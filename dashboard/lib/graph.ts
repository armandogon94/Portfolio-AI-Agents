/**
 * Build a React Flow graph ({nodes, edges}) from a WorkflowInfo (slice-29a).
 *
 * Pure function — no React, no dagre, no side effects. Layout positions
 * are applied separately by lib/dagreLayout.ts so the two concerns stay
 * testable in isolation.
 *
 * See DECISIONS.md DEC-30 for the "registry is the source of truth" decision.
 */

import type { Edge, Node } from "@xyflow/react";

import type { WorkflowInfo } from "./types";

export type AgentNodeKind = "agent" | "manager" | "specialist";

export interface AgentNodeData extends Record<string, unknown> {
  role: string;
  kind: AgentNodeKind;
  rank: number;
}

export type AgentNode = Node<AgentNodeData, "agent">;

export type WorkflowEdgeKind = "sequential" | "delegation" | "fan-in";

export interface WorkflowEdgeData extends Record<string, unknown> {
  kind: WorkflowEdgeKind;
}

export type WorkflowEdge = Edge<WorkflowEdgeData>;

export class UnknownProcessError extends Error {
  constructor(process: string) {
    super(
      `Unknown workflow process '${process}'. Expected 'sequential' or 'hierarchical'.`,
    );
    this.name = "UnknownProcessError";
  }
}

const EDGE_TYPE = "animated";

/**
 * Build React Flow nodes + edges for a workflow.
 *
 * Rules (DEC-30 / SPEC § "Layout rules"):
 *   - sequential, no parallel_tasks  → rank per task; edges task_i → task_{i+1}
 *   - sequential, with parallel_tasks → parallel members share a rank;
 *                                       each parallel member fans-in to the
 *                                       next non-parallel task
 *   - hierarchical                    → manager at rank 0; specialists at rank 1;
 *                                       delegation edges manager → each specialist
 */
export function buildGraph(workflow: WorkflowInfo): {
  nodes: AgentNode[];
  edges: WorkflowEdge[];
} {
  if (!workflow.task_names.length) {
    return { nodes: [], edges: [] };
  }

  if (workflow.process === "hierarchical") {
    return buildHierarchical(workflow);
  }
  if (workflow.process === "sequential") {
    return buildSequential(workflow);
  }
  throw new UnknownProcessError(workflow.process);
}

function buildSequential(workflow: WorkflowInfo): {
  nodes: AgentNode[];
  edges: WorkflowEdge[];
} {
  const parallelGroups = workflow.parallel_tasks ?? [];
  const parallelSet = new Set<string>(parallelGroups.flat());

  // Walk task_names, assigning a rank per task. Tasks in the same parallel
  // group share a rank; non-parallel tasks get their own rank.
  const taskRank = new Map<string, number>();
  let rank = 0;
  const seenParallelAtRank = new Set<number>();
  for (const task of workflow.task_names) {
    if (parallelSet.has(task)) {
      // Group members all live at the same rank; find-or-assign.
      const group = parallelGroups.find((g) => g.includes(task))!;
      const existing = group
        .map((t) => taskRank.get(t))
        .find((r) => r !== undefined);
      if (existing === undefined) {
        // First task of this group we see — claim the current rank.
        if (seenParallelAtRank.has(rank)) rank++;
        group.forEach((t) => taskRank.set(t, rank));
        seenParallelAtRank.add(rank);
        rank++;
      }
      // else: already placed by an earlier member
    } else {
      taskRank.set(task, rank);
      rank++;
    }
  }

  // Nodes keyed by agent role (not task name) — one card per role.
  const roleRank = mapAgentRanks(workflow.agent_roles, taskRank, workflow.task_names);
  const nodes: AgentNode[] = workflow.agent_roles.map((role) => ({
    id: role,
    type: "agent",
    position: { x: 0, y: 0 }, // dagre fills in later
    data: { role, kind: "agent", rank: roleRank.get(role) ?? 0 },
  }));

  // Edges: for every adjacent pair of ranks, connect each agent at the
  // earlier rank to each agent at the later rank that it actually
  // precedes (within this workflow's linear task order).
  const edges: WorkflowEdge[] = [];
  const roleByTask = new Map<string, string>();
  workflow.task_names.forEach((task, idx) => {
    const role = inferTaskRole(workflow, task, idx);
    if (role) roleByTask.set(task, role);
  });

  for (let i = 0; i < workflow.task_names.length - 1; i++) {
    const currentTask = workflow.task_names[i];
    const nextTask = workflow.task_names[i + 1];
    const currentRank = taskRank.get(currentTask);
    const nextRank = taskRank.get(nextTask);
    if (currentRank === nextRank) continue; // same parallel group
    const source = roleByTask.get(currentTask);
    const target = roleByTask.get(nextTask);
    if (!source || !target || source === target) continue;
    const kind: WorkflowEdgeKind = parallelSet.has(currentTask)
      ? "fan-in"
      : "sequential";
    pushUniqueEdge(edges, source, target, kind);
  }

  // Handle fan-in for parallel tasks where the "next task" across the
  // group boundary might not be the immediate successor of every group
  // member in task_names order.
  for (const group of parallelGroups) {
    // Find the first non-parallel task that comes AFTER any group member.
    const groupLastIdx = Math.max(
      ...group.map((t) => workflow.task_names.indexOf(t)),
    );
    const nextTask = workflow.task_names[groupLastIdx + 1];
    if (!nextTask) continue;
    const target = roleByTask.get(nextTask);
    if (!target) continue;
    for (const memberTask of group) {
      const source = roleByTask.get(memberTask);
      if (!source || source === target) continue;
      pushUniqueEdge(edges, source, target, "fan-in");
    }
  }

  return { nodes, edges };
}

function buildHierarchical(workflow: WorkflowInfo): {
  nodes: AgentNode[];
  edges: WorkflowEdge[];
} {
  const managerRole =
    workflow.manager_agent ??
    // Fallback: infer from the first task's agent.
    inferTaskRole(workflow, workflow.task_names[0], 0);

  const nodes: AgentNode[] = workflow.agent_roles.map((role) => ({
    id: role,
    type: "agent",
    position: { x: 0, y: 0 },
    data: {
      role,
      kind: role === managerRole ? "manager" : "specialist",
      rank: role === managerRole ? 0 : 1,
    },
  }));

  const edges: WorkflowEdge[] = [];
  if (managerRole) {
    for (const role of workflow.agent_roles) {
      if (role === managerRole) continue;
      pushUniqueEdge(edges, managerRole, role, "delegation");
    }
  }
  return { nodes, edges };
}

/**
 * Best-effort mapping from agent_role → rank, derived from the tasks
 * that agent owns.
 */
function mapAgentRanks(
  agentRoles: string[],
  taskRank: Map<string, number>,
  taskNames: string[],
): Map<string, number> {
  const out = new Map<string, number>();
  for (const role of agentRoles) {
    // Find the first task assigned to this role (by name convention —
    // tasks.yaml binds task.agent = role). Since we don't have that
    // here, fall back to task index = agent index.
    const idx = agentRoles.indexOf(role);
    const task = taskNames[idx];
    if (task && taskRank.has(task)) {
      out.set(role, taskRank.get(task)!);
    } else {
      out.set(role, idx);
    }
  }
  return out;
}

function inferTaskRole(
  workflow: WorkflowInfo,
  task: string,
  idx: number,
): string | undefined {
  // Convention: tasks.yaml binds task -> agent 1:1, and agent_roles is
  // ordered to match the task_names positionally in the workflows we
  // ship today. For the graph layer we index agent_roles by the task's
  // position in task_names. Registry is authoritative, but this
  // derivation lets us stay pure-client.
  return workflow.agent_roles[idx];
}

function pushUniqueEdge(
  edges: WorkflowEdge[],
  source: string,
  target: string,
  kind: WorkflowEdgeKind,
): void {
  const id = `${source}->${target}`;
  if (edges.some((e) => e.id === id)) return;
  edges.push({
    id,
    source,
    target,
    type: EDGE_TYPE,
    data: { kind },
  });
}

/**
 * TypeScript mirrors of src/models/schemas.py (slice-20b).
 * Kept by hand; regenerate from OpenAPI if drift becomes a problem.
 */

export type AgentRunState =
  | "queued"
  | "active"
  | "waiting_on_tool"
  | "waiting_on_agent"
  | "completed"
  | "failed";

export interface AgentStateEvent {
  task_id: string;
  agent_role: string;
  state: AgentRunState;
  detail: string;
  ts: string;
}

export interface WorkflowInfo {
  name: string;
  description: string;
  process: "sequential" | "hierarchical";
  agent_roles: string[];
  task_names: string[];
  parallel_tasks: string[][] | null;
  inputs_schema: Record<string, string>;
  manager_agent?: string | null;
}

export interface CrewRunRequest {
  topic: string;
  domain?: string | null;
  workflow?: string;
  webhook_url?: string | null;
}

export interface CrewRunResponse {
  task_id: string;
  status: string;
}

export interface RunHistoryEntry {
  task_id: string;
  topic: string;
  domain: string | null;
  result: string;
  duration_seconds: number;
  created_at: string;
}

export interface RunHistoryResponse {
  runs: RunHistoryEntry[];
  count: number;
}

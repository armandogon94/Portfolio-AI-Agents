"use client";

import { useMemo, useState } from "react";

import { AgentCard } from "@/components/AgentCard";
import { KanbanColumn } from "@/components/KanbanColumn";
import { TimelineStrip } from "@/components/TimelineStrip";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { useAgentEvents } from "@/lib/sse";
import type { AgentRunState, AgentStateEvent } from "@/lib/types";

type ColumnKey = "queued" | "active" | "waiting" | "done";

interface AgentView {
  role: string;
  state: AgentRunState;
  currentDetail: string;
  log: AgentStateEvent[];
}

function stateColumn(state: AgentRunState): ColumnKey {
  if (state === "queued") return "queued";
  if (state === "active") return "active";
  if (state === "waiting_on_tool" || state === "waiting_on_agent") {
    return "waiting";
  }
  return "done"; // completed, failed
}

function buildAgents(events: AgentStateEvent[]): Record<string, AgentView> {
  const agents: Record<string, AgentView> = {};
  for (const event of events) {
    const role = event.agent_role || "agent";
    // Crew-level events are rendered as a synthetic "crew" card so the
    // user sees the run lifecycle even when no named agent has reported.
    const bucket = agents[role] ?? {
      role,
      state: event.state,
      currentDetail: event.detail,
      log: [],
    };
    bucket.state = event.state;
    bucket.currentDetail = event.detail;
    bucket.log = [...bucket.log, event];
    agents[role] = bucket;
  }
  return agents;
}

export default function RunView({ taskId }: { taskId: string }) {
  const stream = useAgentEvents(taskId);
  const [shareMsg, setShareMsg] = useState<string | null>(null);

  async function copyShareLink() {
    setShareMsg(null);
    try {
      const resp = await fetch("/api/share/mint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        setShareMsg(body.error ?? `Mint failed (${resp.status})`);
        return;
      }
      const body = (await resp.json()) as { url: string };
      await navigator.clipboard.writeText(body.url);
      setShareMsg("Share link copied to clipboard.");
    } catch (err) {
      setShareMsg(err instanceof Error ? err.message : String(err));
    }
  }

  function exportPdf() {
    // Go straight to the backend — it streams application/pdf.
    window.location.href = `${apiClient.apiUrl}/crew/history/${taskId}/pdf`;
  }

  const agents = useMemo(() => buildAgents(stream.events), [stream.events]);

  const columns: Record<ColumnKey, AgentView[]> = {
    queued: [],
    active: [],
    waiting: [],
    done: [],
  };
  for (const agent of Object.values(agents)) {
    columns[stateColumn(agent.state)].push(agent);
  }

  const startedAt = stream.events.length > 0
    ? Date.parse(stream.events[0].ts) || null
    : null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Run <code className="font-mono text-base">{taskId}</code>
          </h1>
          {stream.completed ? (
            <p className="mt-1 text-sm text-zinc-500">
              {stream.status === "failed" ? "Run failed." : "Run complete."}
            </p>
          ) : (
            <p className="mt-1 text-sm text-zinc-500">
              Live events streaming via SSE.
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <TimelineStrip startedAt={startedAt} completed={stream.completed} />
          <Button
            variant="outline"
            size="sm"
            onClick={copyShareLink}
            disabled={!stream.completed}
          >
            Copy Share Link
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportPdf}
            disabled={!stream.completed}
          >
            Export PDF
          </Button>
        </div>
      </header>

      {shareMsg ? (
        <p className="text-sm text-zinc-500" role="status">
          {shareMsg}
        </p>
      ) : null}

      {stream.error && !stream.completed ? (
        <p role="alert" className="text-sm text-amber-600 dark:text-amber-400">
          {stream.error}
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <KanbanColumn title="Queued" testId="column-queued">
          {columns.queued.map((a) => (
            <AgentCard key={a.role} {...a} />
          ))}
        </KanbanColumn>
        <KanbanColumn title="Active" testId="column-active">
          {columns.active.map((a) => (
            <AgentCard key={a.role} {...a} />
          ))}
        </KanbanColumn>
        <KanbanColumn title="Waiting" testId="column-waiting">
          {columns.waiting.map((a) => (
            <AgentCard key={a.role} {...a} />
          ))}
        </KanbanColumn>
        <KanbanColumn title="Done" testId="column-done">
          {columns.done.map((a) => (
            <AgentCard key={a.role} {...a} />
          ))}
        </KanbanColumn>
      </div>
    </div>
  );
}

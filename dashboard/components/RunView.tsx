"use client";

import { useMemo, useState } from "react";

import { AgentCard } from "@/components/AgentCard";
import GraphPane from "@/components/GraphPane";
import { KanbanColumn } from "@/components/KanbanColumn";
import { TimelineStrip } from "@/components/TimelineStrip";
import { Button } from "@/components/ui/button";
import { ViewToggle, useViewMode } from "@/components/ViewToggle";
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
  const [viewMode, setViewMode] = useViewMode("graph");

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
      <header className="flex flex-col gap-4 rounded-xl border border-zinc-200/80 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between dark:border-zinc-800 dark:bg-zinc-900/60">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Live crew run
          </p>
          <h1 className="mt-1 text-xl font-semibold tracking-tight text-zinc-900 sm:text-2xl dark:text-zinc-50">
            {stream.completed
              ? stream.status === "failed"
                ? "Run failed"
                : "Run complete"
              : "Crew is working"}
          </h1>
          <p className="mt-1 truncate font-mono text-[11px] text-zinc-400">
            {taskId}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <ViewToggle mode={viewMode} onChange={setViewMode} />
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

      {viewMode === "graph" ? (
        <GraphPane taskId={taskId} events={stream.events} />
      ) : (
        <div
          data-testid="board-pane"
          className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4"
        >
          <KanbanColumn
            title="Queued"
            testId="column-queued"
            tone="queued"
            count={columns.queued.length}
            emptyLabel="Nothing queued"
          >
            {columns.queued.map((a) => (
              <AgentCard key={a.role} {...a} />
            ))}
          </KanbanColumn>
          <KanbanColumn
            title="Active"
            testId="column-active"
            tone="active"
            count={columns.active.length}
            emptyLabel="No agent working"
          >
            {columns.active.map((a) => (
              <AgentCard key={a.role} {...a} />
            ))}
          </KanbanColumn>
          <KanbanColumn
            title="Waiting"
            testId="column-waiting"
            tone="waiting"
            count={columns.waiting.length}
            emptyLabel="No blockers"
          >
            {columns.waiting.map((a) => (
              <AgentCard key={a.role} {...a} />
            ))}
          </KanbanColumn>
          <KanbanColumn
            title="Done"
            testId="column-done"
            tone="done"
            count={columns.done.length}
            emptyLabel="Nothing finished yet"
          >
            {columns.done.map((a) => (
              <AgentCard key={a.role} {...a} />
            ))}
          </KanbanColumn>
        </div>
      )}
    </div>
  );
}

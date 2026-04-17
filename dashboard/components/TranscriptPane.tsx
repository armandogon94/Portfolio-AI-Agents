"use client";

import { useEffect, useMemo, useState } from "react";

import { AgentTranscriptSection } from "@/components/AgentTranscriptSection";
import type { AgentStateEvent } from "@/lib/types";

/**
 * Right-hand pane (desktop) / bottom drawer (mobile) showing per-agent
 * live output. One <AgentTranscriptSection> per unique agent_role,
 * ordered by the role's first appearance in `events`. Crew-level events
 * are filtered into their own synthetic "Crew" section so lifecycle
 * messages never disappear.
 */

export interface TranscriptPaneProps {
  events: AgentStateEvent[];
}

function groupByRole(
  events: AgentStateEvent[],
): Array<{ role: string; events: AgentStateEvent[] }> {
  const order: string[] = [];
  const byRole = new Map<string, AgentStateEvent[]>();
  for (const event of events) {
    const role = event.agent_role || "agent";
    if (!byRole.has(role)) {
      order.push(role);
      byRole.set(role, []);
    }
    byRole.get(role)!.push(event);
  }
  return order.map((role) => ({ role, events: byRole.get(role) ?? [] }));
}

export function TranscriptPane({ events }: TranscriptPaneProps) {
  const grouped = useMemo(() => groupByRole(events), [events]);

  // The "active" role is the most recent event's agent_role whose state
  // is not a terminal state. Falls back to the last role seen.
  const activeRole = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.state === "active" || e.state === "waiting_on_tool") {
        return e.agent_role || "agent";
      }
    }
    return events[events.length - 1]?.agent_role ?? null;
  }, [events]);

  // Listen for keyboard-driven focus jumps from the graph (slice-29e).
  // Enter on a graph node dispatches graph:focus-role with the role name;
  // we expand + scroll that role's section into view.
  const [focusedRole, setFocusedRole] = useState<string | null>(null);
  useEffect(() => {
    function handler(e: Event) {
      const role = (e as CustomEvent<{ role: string }>).detail?.role;
      if (!role) return;
      setFocusedRole(role);
      const el = document.getElementById(`transcript-${role}`);
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
    window.addEventListener("graph:focus-role", handler);
    return () => window.removeEventListener("graph:focus-role", handler);
  }, []);

  return (
    <aside
      aria-label="Transcript"
      className="flex min-w-0 flex-col gap-3 rounded-xl border border-zinc-200/80 bg-zinc-50/40 p-3 dark:border-zinc-800 dark:bg-zinc-950/40"
    >
      <header className="flex items-baseline justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Transcript
        </h2>
        <span className="font-mono text-[10px] text-zinc-500 dark:text-zinc-400">
          {events.length} event{events.length === 1 ? "" : "s"}
        </span>
      </header>
      {grouped.length === 0 ? (
        <p className="rounded-md border border-dashed border-zinc-300 bg-white p-4 text-center text-xs text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900/60 dark:text-zinc-400">
          No events yet — the crew hasn't reported in.
        </p>
      ) : (
        grouped.map(({ role, events: agentEvents }) => (
          <AgentTranscriptSection
            key={role}
            role={role}
            events={agentEvents}
            isActive={role === activeRole || role === focusedRole}
          />
        ))
      )}
    </aside>
  );
}

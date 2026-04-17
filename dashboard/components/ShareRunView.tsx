"use client";

import { useMemo, useState } from "react";

import GraphPane from "@/components/GraphPane";
import { Scrubber } from "@/components/Scrubber";
import { TranscriptPane } from "@/components/TranscriptPane";
import type { AgentStateEvent } from "@/lib/types";

/**
 * Client-side shell for a shared run (slice-29d).
 *
 * Given the JSON payload from GET /share/{token}?format=json, renders
 * the Scrubber, GraphPane and TranscriptPane in the same dual-pane
 * layout as the live /runs/[id] view. The scrubber controls an event
 * prefix that both panes consume, so dragging back in time rewinds the
 * graph animation and the transcript together.
 */

export interface SharePayload {
  task_id: string;
  topic: string;
  domain: string | null;
  workflow: string;
  status: string;
  duration_seconds: number;
  result: string;
  events: AgentStateEvent[];
}

export function ShareRunView({ payload }: { payload: SharePayload }) {
  const total = payload.events.length;
  const [scrubberIndex, setScrubberIndex] = useState<number>(total);

  const visibleEvents = useMemo(
    () => payload.events.slice(0, scrubberIndex),
    [payload.events, scrubberIndex],
  );

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-8 sm:px-6">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Shared run
        </p>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-900 sm:text-2xl dark:text-zinc-50">
          {payload.topic}
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500 dark:text-zinc-400">
          {payload.domain ? <span>Domain: {payload.domain}</span> : null}
          <span>Workflow: {payload.workflow}</span>
          <span>Duration: {payload.duration_seconds.toFixed(1)}s</span>
          <span>Status: {payload.status}</span>
        </div>
      </header>

      <Scrubber
        events={payload.events}
        index={scrubberIndex}
        onChange={setScrubberIndex}
      />

      <div className="grid gap-4 md:grid-cols-[1fr_380px]">
        <GraphPane
          taskId={payload.task_id}
          workflowName={payload.workflow}
          events={visibleEvents}
        />
        <TranscriptPane events={visibleEvents} />
      </div>

      {payload.result ? (
        <section
          aria-label="Run result"
          className="rounded-xl border border-zinc-200/80 bg-white p-4 text-sm text-zinc-700 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-200"
        >
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Final report
          </h2>
          <pre className="whitespace-pre-wrap font-sans leading-relaxed">
            {payload.result}
          </pre>
        </section>
      ) : null}
    </main>
  );
}

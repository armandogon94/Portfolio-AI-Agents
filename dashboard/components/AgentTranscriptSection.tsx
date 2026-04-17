"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, ChevronRight, Copy } from "lucide-react";

import { AgentIcon } from "@/components/AgentIcon";
import { StateChip } from "@/components/StateChip";
import type { AgentRunState, AgentStateEvent } from "@/lib/types";

/**
 * One collapsible section per agent role (slice-29c).
 *
 * - Auto-expanded when `isActive` is true.
 * - Auto-scrolls to the latest entry while the user hasn't scrolled up
 *   (IntersectionObserver sentinel at the end of the list).
 * - Copy-all writes this agent's concatenated transcript to the clipboard
 *   on explicit user click — no programmatic access.
 * - Renders `event.detail` as text only (no dangerouslySetInnerHTML).
 *   Tool-call events whose detail starts with "tool:" render as a chip.
 */

function prettyRole(role: string): string {
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function latestState(events: AgentStateEvent[]): AgentRunState {
  return events[events.length - 1]?.state ?? "queued";
}

function toolName(detail: string): string | null {
  const match = /^tool:\s*([\w.-]+)/i.exec(detail);
  return match ? match[1] : null;
}

function formatTs(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString(undefined, {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function buildCopyText(role: string, events: AgentStateEvent[]): string {
  const header = `=== ${prettyRole(role)} ===`;
  const lines = events.map((e) => {
    const ts = formatTs(e.ts);
    return `[${ts}] ${e.state}${e.detail ? ` — ${e.detail}` : ""}`;
  });
  return [header, ...lines, ""].join("\n");
}

export interface AgentTranscriptSectionProps {
  role: string;
  events: AgentStateEvent[];
  isActive: boolean;
}

export function AgentTranscriptSection({
  role,
  events,
  isActive,
}: AgentTranscriptSectionProps) {
  const [expanded, setExpanded] = useState<boolean>(isActive);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [copied, setCopied] = useState(false);

  const listRef = useRef<HTMLOListElement | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const state = useMemo(() => latestState(events), [events]);

  // The parent tells us when this role becomes the active one. Reflect
  // that as "expanded" until the user manually toggles.
  useEffect(() => {
    if (isActive) setExpanded(true);
  }, [isActive]);

  // Observe the sentinel at the bottom — when it leaves the viewport the
  // user has scrolled up, so disable auto-scroll until it returns.
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const obs = new IntersectionObserver((entries) => {
      for (const entry of entries) setAutoScroll(entry.isIntersecting);
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // Scroll to bottom on new events while auto-scroll is on.
  useEffect(() => {
    if (!expanded) return;
    if (!autoScroll) return;
    sentinelRef.current?.scrollIntoView({ block: "nearest" });
  }, [events.length, expanded, autoScroll]);

  async function handleCopy() {
    const text = buildCopyText(role, events);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // Clipboard blocked — leave copied=false; UI shows no confirmation.
    }
  }

  const sectionId = `transcript-${role}`;

  return (
    <section
      role="group"
      aria-label={`Transcript for ${prettyRole(role)}`}
      className={[
        "rounded-xl border bg-white shadow-sm dark:bg-zinc-900/60",
        isActive
          ? "border-l-2 border-l-indigo-500 border-zinc-200/80 dark:border-zinc-800"
          : "border-zinc-200/80 dark:border-zinc-800",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <button
          type="button"
          aria-label={`Toggle ${prettyRole(role)} transcript`}
          aria-expanded={expanded}
          aria-controls={sectionId}
          onClick={() => setExpanded((v) => !v)}
          className="flex min-w-0 flex-1 items-center gap-2 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-50"
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-zinc-400" aria-hidden />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-zinc-400" aria-hidden />
          )}
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500/15 to-violet-500/15 text-indigo-700 ring-1 ring-indigo-200/60 dark:text-indigo-300 dark:ring-indigo-500/30">
            <AgentIcon role={role} className="h-3.5 w-3.5" />
          </span>
          <span className="truncate">{prettyRole(role)}</span>
        </button>
        <div className="flex items-center gap-2">
          <StateChip state={state} />
          <button
            type="button"
            aria-label={`Copy ${prettyRole(role)} transcript`}
            onClick={handleCopy}
            className="inline-flex items-center gap-1 rounded-md border border-zinc-200 px-2 py-1 text-[11px] font-medium text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            <Copy className="h-3 w-3" aria-hidden />
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>
      {expanded ? (
        <ol
          id={sectionId}
          ref={listRef}
          className="max-h-64 space-y-2 overflow-y-auto border-t border-zinc-100 px-3 py-3 dark:border-zinc-800"
        >
          {events.map((event, idx) => {
            const tool = toolName(event.detail);
            return (
              <li
                key={`${event.ts}-${idx}`}
                className="flex flex-col gap-1 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400"
              >
                <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                  <span>{formatTs(event.ts)}</span>
                  <span>·</span>
                  <span>{event.state}</span>
                </div>
                {tool ? (
                  <span className="inline-flex w-fit items-center gap-1 rounded-md bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-700 ring-1 ring-indigo-100 dark:bg-indigo-500/10 dark:text-indigo-300 dark:ring-indigo-500/20">
                    [{tool}]
                    {event.detail.length > `tool: ${tool}`.length ? (
                      <span className="text-indigo-600/80 dark:text-indigo-300/80">
                        {event.detail.slice(`tool: ${tool}`.length).trim()}
                      </span>
                    ) : null}
                  </span>
                ) : event.detail ? (
                  <span>{event.detail}</span>
                ) : null}
              </li>
            );
          })}
          <div ref={sentinelRef} aria-hidden />
        </ol>
      ) : null}
    </section>
  );
}

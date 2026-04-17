"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Pause, Play } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { AgentStateEvent } from "@/lib/types";

/**
 * Share-page scrubber (slice-29d).
 *
 * Drag the slider to replay the run's agent_events up to an arbitrary
 * prefix. Play advances automatically at real-time speed derived from
 * the recorded ts deltas, capped at 2×. Keyboard: ← / → step one
 * event, Space toggles play/pause. "Jump to failure" appears when
 * any event has state=failed.
 */

export interface ScrubberProps {
  events: AgentStateEvent[];
  index: number;
  onChange: (next: number) => void;
}

const MAX_STEP_MS = 2_000; // cap a single step at 2s of wall-clock
const MIN_STEP_MS = 80; // don't faster-than-eye

function stepDelay(events: AgentStateEvent[], nextIndex: number): number {
  if (nextIndex <= 1 || nextIndex > events.length) return 500;
  const prev = Date.parse(events[nextIndex - 2].ts);
  const next = Date.parse(events[nextIndex - 1].ts);
  if (Number.isNaN(prev) || Number.isNaN(next)) return 500;
  // Real-time / 2 (2× speed cap); clamped.
  const delta = Math.max(MIN_STEP_MS, Math.min(MAX_STEP_MS, (next - prev) / 2));
  return delta;
}

function firstFailureIndex(events: AgentStateEvent[]): number | null {
  for (let i = 0; i < events.length; i++) {
    if (events[i].state === "failed") return i + 1; // prefix includes it
  }
  return null;
}

export function Scrubber({ events, index, onChange }: ScrubberProps) {
  const total = events.length;
  const [playing, setPlaying] = useState(false);
  const indexRef = useRef(index);
  indexRef.current = index;
  const failureAt = useMemo(() => firstFailureIndex(events), [events]);

  useEffect(() => {
    if (!playing) return;
    if (indexRef.current >= total) {
      setPlaying(false);
      return;
    }
    const delay = stepDelay(events, indexRef.current + 1);
    const id = window.setTimeout(() => {
      const next = indexRef.current + 1;
      onChange(next);
      if (next >= total) setPlaying(false);
    }, delay);
    return () => window.clearTimeout(id);
  }, [playing, index, events, onChange, total]);

  function step(delta: -1 | 1) {
    const next = Math.max(0, Math.min(total, indexRef.current + delta));
    if (next !== indexRef.current) onChange(next);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      step(1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      step(-1);
    } else if (e.key === " " || e.code === "Space") {
      e.preventDefault();
      setPlaying((v) => !v);
    }
  }

  return (
    <div
      data-testid="scrubber"
      role="group"
      aria-label="Run replay scrubber"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className="flex flex-col gap-2 rounded-xl border border-zinc-200/80 bg-white p-4 shadow-sm outline-none focus:ring-2 focus:ring-indigo-500 dark:border-zinc-800 dark:bg-zinc-900/60"
    >
      <div className="flex items-center gap-3">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setPlaying((v) => !v)}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <Pause className="h-3.5 w-3.5" aria-hidden />
          ) : (
            <Play className="h-3.5 w-3.5" aria-hidden />
          )}
          <span className="ml-1 text-xs">{playing ? "Pause" : "Play"}</span>
        </Button>
        <input
          type="range"
          role="slider"
          aria-label="Scrub run"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={index}
          min={0}
          max={total}
          step={1}
          value={index}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-indigo-500"
        />
        <span className="min-w-[4.5rem] text-right font-mono text-xs text-zinc-500 dark:text-zinc-400">
          {index} / {total}
        </span>
        {failureAt !== null ? (
          <Button
            size="sm"
            variant="outline"
            aria-label="Jump to failure"
            onClick={() => onChange(failureAt)}
            className="text-rose-600 dark:text-rose-400"
          >
            <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
            <span className="ml-1 text-xs">Jump to failure</span>
          </Button>
        ) : null}
      </div>
      <p className="text-[11px] text-zinc-400">
        ← / → step · Space play/pause
      </p>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

export function TimelineStrip({
  startedAt,
  completed,
}: {
  startedAt: number | null;
  completed: boolean;
}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (completed || startedAt === null) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [completed, startedAt]);

  if (startedAt === null) {
    return null;
  }

  const elapsed = Math.max(0, Math.round((now - startedAt) / 1000));

  return (
    <div
      data-testid="timeline-strip"
      className="flex items-center gap-2 text-sm text-zinc-500"
    >
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          completed ? "bg-zinc-400" : "animate-pulse bg-emerald-500"
        }`}
      />
      <span>{completed ? "Finished" : "Running"}</span>
      <span className="font-mono">{elapsed}s</span>
    </div>
  );
}

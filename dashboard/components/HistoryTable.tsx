"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiClient } from "@/lib/api";
import type { RunHistoryEntry } from "@/lib/types";

export default function HistoryTable() {
  const [runs, setRuns] = useState<RunHistoryEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiClient
      .listHistory(20)
      .then((resp) => {
        if (!active) return;
        setRuns(resp.runs);
      })
      .catch((err) => {
        if (!active) return;
        setError(err.message);
      });
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <p role="alert" className="text-sm text-red-600 dark:text-red-400">
        Failed to load history: {error}
      </p>
    );
  }

  if (runs === null) {
    return <p className="text-sm text-zinc-500">Loading history…</p>;
  }

  if (runs.length === 0) {
    return (
      <p className="px-4 py-8 text-center text-sm text-zinc-500">
        No runs yet. Launch one from the home page to populate history.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-zinc-50/70 text-left dark:bg-zinc-900/50">
          <tr>
            <Th>Topic</Th>
            <Th>Domain</Th>
            <Th>Duration</Th>
            <Th>Created</Th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr
              key={run.task_id}
              className="border-t border-zinc-100 transition-colors hover:bg-zinc-50/70 dark:border-zinc-800 dark:hover:bg-zinc-800/40"
            >
              <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-50">
                {run.topic}
              </td>
              <td className="px-4 py-3">
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                  {run.domain ?? "general"}
                </span>
              </td>
              <td className="px-4 py-3 font-mono tabular-nums text-zinc-600 dark:text-zinc-400">
                {run.duration_seconds.toFixed(1)}s
              </td>
              <td className="px-4 py-3 text-zinc-500">
                {new Date(run.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={`/runs/${run.task_id}`}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                >
                  View →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
      {children}
    </th>
  );
}

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
      <p className="text-sm text-zinc-500">
        No runs yet. Launch one from the home page to populate history.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-sm">
        <thead className="bg-zinc-50 text-left dark:bg-zinc-900">
          <tr>
            <th className="px-4 py-2 font-medium">Topic</th>
            <th className="px-4 py-2 font-medium">Domain</th>
            <th className="px-4 py-2 font-medium">Duration</th>
            <th className="px-4 py-2 font-medium">Created</th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr
              key={run.task_id}
              className="border-t border-zinc-200 dark:border-zinc-800"
            >
              <td className="px-4 py-2">{run.topic}</td>
              <td className="px-4 py-2">{run.domain ?? "general"}</td>
              <td className="px-4 py-2">{run.duration_seconds.toFixed(1)}s</td>
              <td className="px-4 py-2 text-zinc-500">
                {new Date(run.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-2 text-right">
                <Link
                  href={`/runs/${run.task_id}`}
                  className="text-zinc-900 underline dark:text-zinc-100"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

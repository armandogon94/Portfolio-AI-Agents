"use client";

import { GitBranch, LayoutGrid } from "lucide-react";
import { useEffect, useState } from "react";

export type ViewMode = "graph" | "board";

const STORAGE_KEY = "view-mode";

export function useViewMode(defaultMode: ViewMode = "graph"): [ViewMode, (m: ViewMode) => void] {
  const [mode, setMode] = useState<ViewMode>(defaultMode);
  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "graph" || saved === "board") setMode(saved);
  }, []);
  const update = (next: ViewMode) => {
    setMode(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // localStorage blocked — fine, stays in-memory for this session.
    }
  };
  return [mode, update];
}

export function ViewToggle({
  mode,
  onChange,
}: {
  mode: ViewMode;
  onChange: (m: ViewMode) => void;
}) {
  return (
    <div
      role="group"
      aria-label="View mode"
      className="inline-flex items-center gap-0.5 rounded-lg border border-zinc-200/80 bg-white p-0.5 text-xs font-medium shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60"
    >
      <Toggle
        active={mode === "graph"}
        onClick={() => onChange("graph")}
        icon={<GitBranch className="h-3.5 w-3.5" aria-hidden />}
      >
        Graph
      </Toggle>
      <Toggle
        active={mode === "board"}
        onClick={() => onChange("board")}
        icon={<LayoutGrid className="h-3.5 w-3.5" aria-hidden />}
      >
        Board
      </Toggle>
    </div>
  );
}

function Toggle({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        "inline-flex items-center gap-1 rounded-md px-2.5 py-1 transition-colors",
        active
          ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
          : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800",
      ].join(" ")}
    >
      {icon}
      {children}
    </button>
  );
}

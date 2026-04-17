import type { AgentRunState } from "@/lib/types";

const STATES: Record<
  AgentRunState,
  { label: string; dot: string; text: string; bg: string; ring: string }
> = {
  queued: {
    label: "Queued",
    dot: "bg-zinc-400",
    text: "text-zinc-700 dark:text-zinc-300",
    bg: "bg-zinc-100 dark:bg-zinc-800/60",
    ring: "ring-zinc-200/70 dark:ring-zinc-700",
  },
  active: {
    label: "Active",
    dot: "bg-emerald-500 animate-pulse",
    text: "text-emerald-800 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-500/10",
    ring: "ring-emerald-200 dark:ring-emerald-500/40",
  },
  waiting_on_tool: {
    label: "Tool",
    dot: "bg-sky-500",
    text: "text-sky-800 dark:text-sky-300",
    bg: "bg-sky-50 dark:bg-sky-500/10",
    ring: "ring-sky-200 dark:ring-sky-500/40",
  },
  waiting_on_agent: {
    label: "Waiting",
    dot: "bg-amber-500",
    text: "text-amber-800 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-500/10",
    ring: "ring-amber-200 dark:ring-amber-500/40",
  },
  completed: {
    label: "Done",
    dot: "bg-indigo-500",
    text: "text-indigo-800 dark:text-indigo-300",
    bg: "bg-indigo-50 dark:bg-indigo-500/10",
    ring: "ring-indigo-200 dark:ring-indigo-500/40",
  },
  failed: {
    label: "Failed",
    dot: "bg-rose-500",
    text: "text-rose-800 dark:text-rose-300",
    bg: "bg-rose-50 dark:bg-rose-500/10",
    ring: "ring-rose-200 dark:ring-rose-500/40",
  },
};

export function StateChip({ state }: { state: AgentRunState }) {
  const s = STATES[state];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${s.bg} ${s.text} ${s.ring}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

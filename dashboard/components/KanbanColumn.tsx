import type { ReactNode } from "react";

import { CheckCircle2, Clock, Loader2, PauseCircle } from "lucide-react";

export type ColumnTone = "queued" | "active" | "waiting" | "done";

const TONES: Record<
  ColumnTone,
  { icon: typeof Clock; iconClass: string; bar: string }
> = {
  queued: {
    icon: Clock,
    iconClass: "text-zinc-500",
    bar: "bg-zinc-400/70",
  },
  active: {
    icon: Loader2,
    iconClass: "text-emerald-600 dark:text-emerald-400",
    bar: "bg-emerald-500",
  },
  waiting: {
    icon: PauseCircle,
    iconClass: "text-amber-600 dark:text-amber-400",
    bar: "bg-amber-500",
  },
  done: {
    icon: CheckCircle2,
    iconClass: "text-indigo-600 dark:text-indigo-400",
    bar: "bg-indigo-500",
  },
};

export interface KanbanColumnProps {
  title: string;
  testId: string;
  tone: ColumnTone;
  count: number;
  children: ReactNode;
  emptyLabel?: string;
}

export function KanbanColumn({
  title,
  testId,
  tone,
  count,
  children,
  emptyLabel = "No agents here yet",
}: KanbanColumnProps) {
  const t = TONES[tone];
  const Icon = t.icon;
  return (
    <section
      data-testid={testId}
      className="flex min-h-[14rem] flex-1 flex-col overflow-hidden rounded-xl border border-zinc-200/80 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60"
    >
      <div className={`h-0.5 w-full ${t.bar}`} aria-hidden />
      <header className="flex items-center justify-between border-b border-zinc-100 px-4 py-3 dark:border-zinc-800">
        <div className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${t.iconClass}`} aria-hidden />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-600 dark:text-zinc-300">
            {title}
          </h2>
        </div>
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] font-medium tabular-nums text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          {count}
        </span>
      </header>
      <div className="flex flex-1 flex-col gap-3 p-3">
        {count > 0 ? (
          children
        ) : (
          <p className="rounded-md border border-dashed border-zinc-200 px-3 py-6 text-center text-xs text-zinc-400 dark:border-zinc-800 dark:text-zinc-500">
            {emptyLabel}
          </p>
        )}
      </div>
    </section>
  );
}

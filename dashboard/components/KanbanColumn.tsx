import type { ReactNode } from "react";

export interface KanbanColumnProps {
  title: string;
  testId: string;
  children: ReactNode;
}

export function KanbanColumn({ title, testId, children }: KanbanColumnProps) {
  return (
    <section
      data-testid={testId}
      className="flex min-h-[8rem] flex-1 flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <header className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
        {title}
      </header>
      <div className="flex flex-col gap-3">{children}</div>
    </section>
  );
}

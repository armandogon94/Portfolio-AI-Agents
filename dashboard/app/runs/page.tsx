import HistoryTable from "@/components/HistoryTable";

export default function RunsHistoryPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 px-4 py-10 sm:px-6">
      <header className="mx-auto w-full max-w-5xl">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Archive
        </p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Run history
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Recent crew runs, newest first.
        </p>
      </header>
      <section className="mx-auto w-full max-w-5xl rounded-xl border border-zinc-200/80 bg-white p-1 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
        <HistoryTable />
      </section>
    </main>
  );
}

import HistoryTable from "@/components/HistoryTable";

export default function RunsHistoryPage() {
  return (
    <main className="flex flex-1 flex-col gap-8 bg-zinc-50 px-6 py-16 font-sans dark:bg-zinc-950">
      <header className="mx-auto w-full max-w-5xl">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Run history
        </h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Recent crew runs (most recent first).
        </p>
      </header>
      <section className="mx-auto w-full max-w-5xl">
        <HistoryTable />
      </section>
    </main>
  );
}

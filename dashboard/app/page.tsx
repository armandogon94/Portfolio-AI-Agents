export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 bg-zinc-50 px-6 py-24 font-sans dark:bg-zinc-950">
      <div className="max-w-2xl text-center sm:text-left">
        <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
          AI Agent Team Dashboard
        </h1>
        <p className="mt-4 text-lg leading-8 text-zinc-600 dark:text-zinc-400">
          Launch a workflow, watch the crew work, review completed runs. Connected
          to the FastAPI backend at{" "}
          <code className="rounded bg-zinc-200 px-1 py-0.5 text-sm dark:bg-zinc-800">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060"}
          </code>
          .
        </p>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-500">
          Slice 20a — scaffold. Launcher, history, and live team view land in 20b/20c.
        </p>
      </div>
    </main>
  );
}

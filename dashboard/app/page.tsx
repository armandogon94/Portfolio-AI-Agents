import LauncherForm from "@/components/LauncherForm";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-start gap-10 bg-zinc-50 px-6 py-16 font-sans dark:bg-zinc-950">
      <header className="max-w-2xl text-center sm:text-left">
        <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
          AI Agent Team Dashboard
        </h1>
        <p className="mt-4 text-lg leading-8 text-zinc-600 dark:text-zinc-400">
          Launch a workflow, watch the crew work, review completed runs.
        </p>
      </header>
      <LauncherForm />
    </main>
  );
}

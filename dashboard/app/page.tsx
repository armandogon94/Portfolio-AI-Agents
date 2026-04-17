import { Sparkles } from "lucide-react";

import LauncherForm from "@/components/LauncherForm";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center px-4 py-12 sm:px-6">
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-8">
        <header className="flex flex-col items-center gap-3 text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200/70 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 dark:border-indigo-500/30 dark:bg-indigo-500/10 dark:text-indigo-300">
            <Sparkles className="h-3.5 w-3.5" aria-hidden />
            Multi-agent crew, running locally
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
            AI Agent Team Dashboard
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-zinc-600 dark:text-zinc-400">
            Pick a pre-built crew, drop in a topic, and watch the team work —
            live kanban, share links, and PDF exports included.
          </p>
        </header>
        <LauncherForm />
      </div>
    </main>
  );
}

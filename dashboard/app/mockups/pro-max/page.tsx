/**
 * Mockup — UI-UX Pro Max (Refactoring UI on shadcn).
 *
 * Signatures: constrained scales, generous whitespace, label/value
 * hierarchy (small uppercase labels, darker larger values), muted
 * grays with purposeful indigo accents, subtle two-layer shadow,
 * dividers only where they earn their keep. Self-contained — delete
 * the file to remove.
 */

import Link from "next/link";

export default function ProMaxMockup() {
  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50">
      <div className="mx-auto max-w-6xl px-8 py-12">
        <nav className="mb-12 flex items-center justify-between text-xs text-zinc-500">
          <Link href="/mockups" className="hover:text-zinc-900 dark:hover:text-zinc-200">
            ← Mockups
          </Link>
          <span className="font-semibold uppercase tracking-[0.14em] text-zinc-400">
            UI-UX Pro Max
          </span>
        </nav>

        <header className="mb-12 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600 dark:text-indigo-400">
            Multi-agent crew, running locally
          </p>
          <h1 className="mt-3 text-4xl font-semibold leading-[1.1] tracking-tight">
            AI Agent Team Dashboard
          </h1>
          <p className="mt-4 text-[15px] leading-relaxed text-zinc-600 dark:text-zinc-400">
            Pick a pre-built crew, drop in a topic, and watch the team work —
            live animation, share links, and PDF exports included.
          </p>
        </header>

        <div className="grid gap-8 lg:grid-cols-[1.15fr_1fr]">
          {/* Launcher card */}
          <section className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_10px_30px_-10px_rgba(24,24,27,0.08)] dark:border-zinc-800 dark:bg-zinc-900">
            <div className="mb-8 flex items-baseline justify-between">
              <h2 className="text-xl font-semibold tracking-tight">
                Launch a crew
              </h2>
              <span className="text-xs text-zinc-500">~2 min demo</span>
            </div>

            <div className="space-y-6">
              <LabelValue label="Workflow">
                <div className="flex flex-col gap-2">
                  <SelectRow value="Research Report" meta="4 agents · Sequential" selected />
                  <SelectRow value="Competitive Research" meta="3 agents · Hierarchical" />
                  <SelectRow value="Support Triage" meta="3 agents · Hierarchical" />
                </div>
              </LabelValue>

              <Divider />

              <LabelValue label="Domain">
                <div className="flex flex-wrap gap-1.5">
                  {["General", "Finance", "Healthcare", "Real Estate", "Legal"].map(
                    (d) => (
                      <Chip key={d} active={d === "Finance"}>
                        {d}
                      </Chip>
                    ),
                  )}
                </div>
              </LabelValue>

              <Divider />

              <LabelValue label="Topic">
                <div className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-[15px] text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50">
                  AI-powered personalization in luxury retail 2026
                </div>
              </LabelValue>

              <button className="w-full rounded-lg bg-zinc-900 py-3 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.12)] transition hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-white">
                Launch crew
              </button>
            </div>
          </section>

          {/* Live run summary */}
          <section className="flex flex-col gap-4">
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_10px_30px_-10px_rgba(24,24,27,0.08)] dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-5 flex items-center justify-between">
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  Live run
                </h3>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Running
                </span>
              </div>

              <div className="space-y-3">
                <NodeRow role="Researcher" detail="Pulled 14 sources" state="done" />
                <NodeRow
                  role="Analyst"
                  detail="Cross-referencing competitors…"
                  state="active"
                />
                <NodeRow role="Writer" detail="Queued" state="queued" />
                <NodeRow role="Validator" detail="Queued" state="queued" />
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_10px_30px_-10px_rgba(24,24,27,0.08)] dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-baseline justify-between">
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  Duration
                </h3>
                <span className="text-xs text-zinc-400">so far</span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <p className="text-4xl font-semibold tabular-nums tracking-tight">
                  42.1
                </p>
                <span className="text-sm text-zinc-500">seconds</span>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Median for this workflow: <span className="font-medium text-zinc-700 dark:text-zinc-300">38s</span>
              </p>
            </div>
          </section>
        </div>

        <p className="mt-12 text-center text-xs text-zinc-400">
          Mockup only · UI-UX Pro Max · delete when done
        </p>
      </div>
    </div>
  );
}

function LabelValue({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
        {label}
      </p>
      {children}
    </div>
  );
}

function SelectRow({
  value,
  meta,
  selected,
}: {
  value: string;
  meta: string;
  selected?: boolean;
}) {
  return (
    <button
      className={[
        "flex items-center justify-between rounded-lg border px-4 py-3 text-left transition",
        selected
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-50 dark:bg-zinc-50 dark:text-zinc-900"
          : "border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700",
      ].join(" ")}
    >
      <div>
        <p className="text-sm font-semibold">{value}</p>
        <p
          className={[
            "mt-0.5 text-xs",
            selected ? "text-zinc-300 dark:text-zinc-500" : "text-zinc-500",
          ].join(" ")}
        >
          {meta}
        </p>
      </div>
      {selected ? (
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : null}
    </button>
  );
}

function Chip({
  active,
  children,
}: {
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      className={[
        "rounded-full border px-3 py-1 text-xs font-medium transition",
        active
          ? "border-indigo-600 bg-indigo-50 text-indigo-700 dark:border-indigo-400 dark:bg-indigo-500/10 dark:text-indigo-300"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function Divider() {
  return <div className="h-px bg-zinc-100 dark:bg-zinc-800" />;
}

function NodeRow({
  role,
  detail,
  state,
}: {
  role: string;
  detail: string;
  state: "queued" | "active" | "done";
}) {
  const dot =
    state === "active"
      ? "bg-indigo-500 ring-4 ring-indigo-200 dark:ring-indigo-500/30"
      : state === "done"
        ? "bg-emerald-500"
        : "bg-zinc-300 dark:bg-zinc-700";
  return (
    <div className="flex items-center gap-3 rounded-lg border border-zinc-100 bg-zinc-50/60 px-3 py-2.5 dark:border-zinc-800/60 dark:bg-zinc-800/40">
      <span className={["h-2 w-2 shrink-0 rounded-full", dot].join(" ")} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{role}</p>
        <p className="truncate text-xs text-zinc-500">{detail}</p>
      </div>
      <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
        {state}
      </span>
    </div>
  );
}

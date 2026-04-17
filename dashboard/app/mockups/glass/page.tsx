/**
 * Mockup — Liquid Glass (Apple 2025 translucency direction).
 *
 * Signatures: frosted panels (backdrop-filter), specular top border,
 * saturated background gradient showing through, soft inner shadows,
 * vibrant accent ring. Everything is self-contained — delete this file
 * to remove the mockup.
 */

import Link from "next/link";

export default function GlassMockup() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_10%_20%,#a5b4fc_0%,transparent_40%),radial-gradient(circle_at_90%_10%,#f0abfc_0%,transparent_40%),radial-gradient(circle_at_50%_90%,#67e8f9_0%,transparent_45%)] bg-zinc-950 text-zinc-900">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <nav className="mb-10 flex items-center justify-between">
          <Link
            href="/mockups"
            className="text-xs text-white/70 hover:text-white"
          >
            ← Back to mockups
          </Link>
          <span className="rounded-full border border-white/25 bg-white/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-white/80 backdrop-blur-md">
            Liquid Glass
          </span>
        </nav>

        <header className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/70">
            Multi-agent crew, running locally
          </p>
          <h1
            className="mt-3 text-5xl font-semibold tracking-tight text-white"
            style={{ fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif" }}
          >
            AI Agent Team
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/75">
            Pick a pre-built crew, drop in a topic, and watch the team work.
            Live animation, share links, and PDF exports included.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          {/* Launch card */}
          <section className="relative overflow-hidden rounded-[28px] border border-white/25 bg-white/10 p-6 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
            {/* Specular highlight */}
            <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-white/60 to-transparent" />
            <h2 className="text-xl font-semibold text-white">Launch a crew</h2>
            <p className="mt-1 text-sm text-white/70">
              Runs entirely on your machine when DEMO_MODE is on.
            </p>

            <div className="mt-6 space-y-5">
              <Field label="Workflow">
                <Pill active>Research Report</Pill>
                <Pill>Competitive Research</Pill>
                <Pill>Support Triage</Pill>
                <Pill>Sales Qualification</Pill>
              </Field>

              <Field label="Domain">
                <Pill>General</Pill>
                <Pill active>Finance</Pill>
                <Pill>Healthcare</Pill>
                <Pill>Real Estate</Pill>
                <Pill>Legal</Pill>
              </Field>

              <Field label="Topic">
                <div className="w-full rounded-2xl border border-white/20 bg-white/10 px-4 py-3 text-sm text-white/90 backdrop-blur-md placeholder:text-white/50">
                  AI-powered personalization in luxury retail 2026
                </div>
              </Field>

              <button className="w-full rounded-2xl bg-gradient-to-b from-white/95 to-white/80 px-4 py-3 text-sm font-semibold text-indigo-900 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.9),0_12px_30px_-10px_rgba(99,102,241,0.6)] ring-1 ring-white/40 transition hover:from-white hover:to-white">
                Launch crew
              </button>
            </div>
          </section>

          {/* Mini graph preview */}
          <section className="relative overflow-hidden rounded-[28px] border border-white/25 bg-white/10 p-6 backdrop-blur-2xl">
            <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-white/60 to-transparent" />
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-white/80">
                Live graph
              </h3>
              <span className="rounded-full border border-emerald-300/40 bg-emerald-300/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-200 backdrop-blur-md">
                Running
              </span>
            </div>
            <div className="mt-6 flex items-center justify-between gap-3">
              <GlassNode label="Researcher" state="done" />
              <Arrow active />
              <GlassNode label="Analyst" state="active" />
              <Arrow />
              <GlassNode label="Writer" state="queued" />
              <Arrow />
              <GlassNode label="Validator" state="queued" />
            </div>

            <div className="mt-6 space-y-2">
              <TranscriptLine
                role="Researcher"
                state="done"
                detail="Pulled 14 sources from Google News."
              />
              <TranscriptLine
                role="Analyst"
                state="active"
                detail="Cross-referencing competitive positioning…"
                active
              />
            </div>
          </section>
        </div>

        <p className="mt-10 text-center text-xs text-white/40">
          Mockup only · Liquid Glass · delete when done
        </p>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-white/60">
        {label}
      </p>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

function Pill({
  active,
  children,
}: {
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      className={[
        "rounded-full px-3.5 py-1.5 text-xs font-medium backdrop-blur-md transition",
        active
          ? "border border-white/40 bg-white/20 text-white shadow-[inset_0_1px_0_0_rgba(255,255,255,0.5)]"
          : "border border-white/15 bg-white/5 text-white/75 hover:bg-white/10",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function GlassNode({
  label,
  state,
}: {
  label: string;
  state: "queued" | "active" | "done";
}) {
  const ring =
    state === "active"
      ? "ring-2 ring-indigo-300/70 shadow-[0_0_30px_-6px_rgba(165,180,252,0.9)]"
      : state === "done"
        ? "ring-1 ring-emerald-300/50"
        : "ring-1 ring-white/15";
  return (
    <div
      className={[
        "flex min-w-[110px] flex-col items-center gap-1 rounded-2xl border border-white/20 bg-white/10 px-3 py-3 text-center backdrop-blur-md",
        ring,
      ].join(" ")}
    >
      <span className="text-sm font-semibold text-white">{label}</span>
      <span
        className={[
          "text-[10px] font-semibold uppercase tracking-wider",
          state === "active"
            ? "text-indigo-200"
            : state === "done"
              ? "text-emerald-200"
              : "text-white/50",
        ].join(" ")}
      >
        {state}
      </span>
    </div>
  );
}

function Arrow({ active }: { active?: boolean }) {
  return (
    <span
      className={[
        "h-px flex-1",
        active
          ? "bg-gradient-to-r from-emerald-300/80 via-indigo-300/80 to-white/20"
          : "bg-white/15",
      ].join(" ")}
    />
  );
}

function TranscriptLine({
  role,
  state,
  detail,
  active,
}: {
  role: string;
  state: string;
  detail: string;
  active?: boolean;
}) {
  return (
    <div
      className={[
        "flex items-start gap-3 rounded-xl border border-white/15 bg-white/5 p-3 text-xs text-white/85 backdrop-blur-md",
        active ? "border-indigo-300/40 bg-indigo-400/10" : "",
      ].join(" ")}
    >
      <span className="w-20 shrink-0 text-[10px] font-semibold uppercase tracking-wider text-white/60">
        {role}
      </span>
      <span className="grow">{detail}</span>
      <span className="shrink-0 text-[10px] uppercase tracking-wider text-white/50">
        {state}
      </span>
    </div>
  );
}

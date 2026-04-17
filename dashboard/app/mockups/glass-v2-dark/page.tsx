/**
 * Glass v2 — Dark Mono.
 *
 * Contrast strategy: warm near-black canvas with ONE large soft light
 * bloom behind the frost. Glass panels are dark-on-dark so all body text
 * lands on a dark base, guaranteeing ≥7:1 contrast. No rainbow gradient.
 * Single signature accent (amber). Display type is Instrument Serif at
 * architectural scale (top-design §1), body is Space Grotesk at 16px.
 *
 * Delete this file to remove the mockup.
 */

import Link from "next/link";
import { Instrument_Serif, Space_Grotesk } from "next/font/google";

const display = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--mockup-display",
});
const body = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--mockup-body",
});

export default function GlassDark() {
  return (
    <div
      className={`${display.variable} ${body.variable} min-h-screen bg-[#0b0b0d] text-[#fafaf9]`}
      style={{ fontFamily: "var(--mockup-body)" }}
    >
      {/* Single ambient light — one blob, one color, one direction.
          Replaces the rainbow mishmash. */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-[-20%] h-[70vh] w-[70vw] rounded-full bg-[#f59e0b] opacity-[0.18] blur-[140px]" />
        <div className="absolute right-[-15%] bottom-[-30%] h-[60vh] w-[60vw] rounded-full bg-[#ea580c] opacity-[0.10] blur-[160px]" />
      </div>

      <div className="relative mx-auto max-w-[1280px] px-8 py-10">
        <nav className="mb-20 flex items-center justify-between text-xs text-[#c9c9c4]/70">
          <Link href="/mockups" className="hover:text-[#fafaf9]">
            ← Mockups
          </Link>
          <span className="font-semibold uppercase tracking-[0.18em] text-[#f59e0b]">
            Glass · Dark Mono
          </span>
        </nav>

        {/* Hero — asymmetric, offset from center, massive scale contrast */}
        <header className="mb-24 grid grid-cols-12 gap-6">
          <div className="col-span-12 md:col-span-8 md:col-start-2">
            <p className="mb-6 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#c9c9c4]/60">
              Multi-agent crew · v4.1
            </p>
            <h1
              className="text-[84px] leading-[0.95] tracking-[-0.03em] text-[#fafaf9] md:text-[128px]"
              style={{ fontFamily: "var(--mockup-display)" }}
            >
              Watch the <em className="text-[#f59e0b]">team</em> work.
            </h1>
            <p className="mt-10 max-w-md text-[15px] leading-[1.65] text-[#c9c9c4]/85">
              Pick a pre-built crew, drop in a topic, and see four agents
              research, analyse, draft and validate — live on a single page.
            </p>
          </div>
        </header>

        {/* Launcher + Live — offset 12-column grid, not centered */}
        <div className="grid grid-cols-12 gap-6">
          {/* Launcher card */}
          <section className="col-span-12 md:col-span-7 md:col-start-2">
            <GlassPanel>
              <div className="mb-8 flex items-baseline justify-between">
                <h2
                  className="text-3xl tracking-tight text-[#fafaf9]"
                  style={{ fontFamily: "var(--mockup-display)" }}
                >
                  Launch a crew
                </h2>
                <span className="text-[11px] uppercase tracking-[0.18em] text-[#c9c9c4]/60">
                  Step 1 of 1
                </span>
              </div>

              <FieldLabel>Workflow</FieldLabel>
              <div className="mb-8 grid gap-2">
                <WorkflowRow
                  title="Research Report"
                  meta="4 agents · Sequential"
                  selected
                />
                <WorkflowRow
                  title="Competitive Research"
                  meta="3 agents · Hierarchical"
                />
                <WorkflowRow
                  title="Support Triage"
                  meta="3 agents · Hierarchical"
                />
              </div>

              <FieldLabel>Domain</FieldLabel>
              <div className="mb-8 flex flex-wrap gap-1.5">
                {[
                  "General",
                  "Finance",
                  "Healthcare",
                  "Real Estate",
                  "Legal",
                  "Education",
                ].map((d) => (
                  <Chip key={d} active={d === "Finance"}>
                    {d}
                  </Chip>
                ))}
              </div>

              <FieldLabel>Topic</FieldLabel>
              <div className="mb-8 border-b border-[#fafaf9]/25 pb-3 text-[18px] text-[#fafaf9]">
                AI-powered personalization in luxury retail 2026
              </div>

              <button className="group flex w-full items-center justify-between rounded-full bg-[#f59e0b] px-6 py-4 text-[15px] font-semibold text-[#0b0b0d] transition hover:bg-[#fbbf24]">
                <span>Launch crew</span>
                <span aria-hidden className="transition group-hover:translate-x-1">
                  →
                </span>
              </button>
            </GlassPanel>
          </section>

          {/* Live run */}
          <section className="col-span-12 md:col-span-3">
            <GlassPanel subtle>
              <div className="mb-5 flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9c9c4]/70">
                  Live run
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f59e0b]/15 px-2 py-0.5 text-[10px] font-semibold text-[#fbbf24]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#f59e0b]" />
                  Running
                </span>
              </div>
              <div className="space-y-2">
                <AgentRow role="Researcher" state="done" />
                <AgentRow role="Analyst" state="active" />
                <AgentRow role="Writer" state="queued" />
                <AgentRow role="Validator" state="queued" />
              </div>

              <div className="mt-6 border-t border-[#fafaf9]/10 pt-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9c9c4]/60">
                  Elapsed
                </p>
                <p
                  className="mt-1 text-[44px] tabular-nums leading-none tracking-tight text-[#fafaf9]"
                  style={{ fontFamily: "var(--mockup-display)" }}
                >
                  42.1<span className="text-lg text-[#c9c9c4]/60">s</span>
                </p>
              </div>
            </GlassPanel>
          </section>
        </div>

        <p className="mt-20 text-center text-xs text-[#c9c9c4]/40">
          Mockup only · Glass v2 Dark Mono · delete when done
        </p>
      </div>
    </div>
  );
}

function GlassPanel({
  children,
  subtle,
}: {
  children: React.ReactNode;
  subtle?: boolean;
}) {
  return (
    <div
      className={[
        "relative overflow-hidden rounded-3xl border p-8",
        subtle
          ? "border-[#fafaf9]/8 bg-[#18181a]/50"
          : "border-[#fafaf9]/12 bg-[#18181a]/60",
      ].join(" ")}
      style={{ backdropFilter: "blur(28px) saturate(140%)" }}
    >
      {/* Specular highlight (top-design §3 details) */}
      <div className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-[#fafaf9]/35 to-transparent" />
      {children}
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-[#c9c9c4]/65">
      {children}
    </p>
  );
}

function WorkflowRow({
  title,
  meta,
  selected,
}: {
  title: string;
  meta: string;
  selected?: boolean;
}) {
  return (
    <button
      className={[
        "group flex w-full items-center justify-between rounded-2xl border px-5 py-4 text-left transition",
        selected
          ? "border-[#f59e0b]/60 bg-[#f59e0b]/10"
          : "border-[#fafaf9]/10 bg-[#fafaf9]/[0.03] hover:border-[#fafaf9]/25 hover:bg-[#fafaf9]/[0.05]",
      ].join(" ")}
    >
      <div>
        <p
          className={[
            "text-[17px] tracking-tight",
            selected ? "text-[#fbbf24]" : "text-[#fafaf9]",
          ].join(" ")}
        >
          {title}
        </p>
        <p className="mt-0.5 text-[12px] text-[#c9c9c4]/65">{meta}</p>
      </div>
      {selected ? (
        <span className="text-[#f59e0b]">●</span>
      ) : (
        <span className="text-[#fafaf9]/30 transition group-hover:text-[#fafaf9]/60">
          →
        </span>
      )}
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
        "rounded-full border px-3.5 py-1.5 text-[12px] font-medium transition",
        active
          ? "border-[#f59e0b]/70 bg-[#f59e0b]/15 text-[#fbbf24]"
          : "border-[#fafaf9]/12 bg-transparent text-[#c9c9c4]/80 hover:border-[#fafaf9]/30 hover:text-[#fafaf9]",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function AgentRow({
  role,
  state,
}: {
  role: string;
  state: "queued" | "active" | "done";
}) {
  const dot =
    state === "active"
      ? "bg-[#f59e0b] ring-4 ring-[#f59e0b]/25"
      : state === "done"
        ? "bg-[#c9c9c4]/70"
        : "bg-[#fafaf9]/20";
  return (
    <div className="flex items-center gap-3 rounded-xl border border-[#fafaf9]/8 bg-[#fafaf9]/[0.02] px-3 py-2.5">
      <span className={["h-2 w-2 shrink-0 rounded-full", dot].join(" ")} />
      <span className="flex-1 text-[13px] text-[#fafaf9]">{role}</span>
      <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#c9c9c4]/60">
        {state}
      </span>
    </div>
  );
}

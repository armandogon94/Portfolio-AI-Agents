/**
 * Glass v2 — Adaptive split-screen.
 *
 * Contrast strategy: the page is literally two halves meeting at a
 * seam — left is warm-dark (#0c0c0e), right is warm-cream (#f5f1e8).
 * Each half uses a glass treatment tuned for its base: dark-on-dark
 * frost on the left, light-on-light frost on the right. The signature
 * moment is a giant typographic headline that splits across the seam,
 * its color inverting at the midpoint. Single accent: electric lime.
 *
 * Demonstrates that "liquid glass" doesn't have to mean "everything
 * translucent on rainbow" — here translucency is a local effect,
 * not the whole page.
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

const DARK = "#0c0c0e";
const DARK_TEXT = "#fafaf9";
const CREAM = "#f5f1e8";
const CREAM_TEXT = "#1a1814";
const LIME = "#bef264"; // lime-300 — single accent

export default function GlassAdaptive() {
  return (
    <div
      className={`${display.variable} ${body.variable} min-h-screen`}
      style={{ fontFamily: "var(--mockup-body)" }}
    >
      {/* Two-tone canvas — split at 48% so the seam lands left-of-center,
          making the composition asymmetric on purpose. */}
      <div className="relative min-h-screen">
        <div className="absolute inset-y-0 left-0 w-[48%]" style={{ background: DARK }} />
        <div className="absolute inset-y-0 left-[48%] right-0" style={{ background: CREAM }} />

        {/* Single ambient light on the dark side */}
        <div
          className="pointer-events-none absolute top-[-10%] left-[-5%] h-[60vh] w-[40vw] rounded-full opacity-[0.22] blur-[120px]"
          style={{ background: LIME }}
        />

        <div className="relative mx-auto max-w-[1440px] px-8 py-10">
          {/* Top nav — spans both halves with adaptive colors */}
          <nav className="mb-24 grid grid-cols-12 items-center text-xs">
            <div className="col-span-6" style={{ color: `${DARK_TEXT}99` }}>
              <Link
                href="/mockups"
                className="transition hover:opacity-80"
                style={{ color: DARK_TEXT }}
              >
                ← Mockups
              </Link>
            </div>
            <div className="col-span-6 text-right">
              <span
                className="font-semibold uppercase tracking-[0.18em]"
                style={{ color: CREAM_TEXT }}
              >
                Glass · Adaptive
              </span>
            </div>
          </nav>

          {/* Signature hero — the word "team" bleeds across the seam.
              Left half renders it in cream; right half renders it in dark.
              Each half clips to its canvas using absolute positioning. */}
          <header className="mb-28">
            <p
              className="mb-6 text-[11px] font-semibold uppercase tracking-[0.22em]"
              style={{ color: `${DARK_TEXT}80` }}
            >
              Two sides of the same run
            </p>
            <div
              className="relative text-[112px] leading-[0.92] tracking-[-0.03em] md:text-[176px]"
              style={{ fontFamily: "var(--mockup-display)" }}
            >
              <span style={{ color: DARK_TEXT }}>
                A single <em style={{ color: LIME, fontStyle: "italic" }}>crew,</em>
              </span>
              <br />
              <span className="relative inline-block">
                {/* Render twice, layered, clipped to their respective halves
                    so the same letterforms read in both tones. */}
                <span
                  className="relative z-0"
                  style={{ color: DARK_TEXT }}
                >
                  two vantage points.
                </span>
                <span
                  aria-hidden
                  className="absolute inset-0 z-10"
                  style={{
                    color: CREAM_TEXT,
                    clipPath: "inset(0 0 0 48%)",
                  }}
                >
                  two vantage points.
                </span>
              </span>
            </div>
          </header>

          {/* Content: left half shows a dark glass launcher card,
              right half shows a light glass live-run card */}
          <div className="grid grid-cols-12 gap-12">
            {/* Left — dark glass */}
            <section className="col-span-12 md:col-span-5">
              <div
                className="relative overflow-hidden rounded-3xl border p-7"
                style={{
                  borderColor: `${DARK_TEXT}15`,
                  background: "rgba(24, 24, 27, 0.62)",
                  backdropFilter: "blur(28px) saturate(140%)",
                }}
              >
                <div
                  className="pointer-events-none absolute inset-x-7 top-0 h-px"
                  style={{
                    background: `linear-gradient(to right, transparent, ${DARK_TEXT}55, transparent)`,
                  }}
                />
                <Label color={`${DARK_TEXT}aa`}>Launch a crew</Label>
                <h2
                  className="mt-2 text-[32px] tracking-tight"
                  style={{ fontFamily: "var(--mockup-display)", color: DARK_TEXT }}
                >
                  Pick, topic, launch.
                </h2>

                <div className="mt-7 space-y-5">
                  <div>
                    <Label color={`${DARK_TEXT}80`}>Workflow</Label>
                    <div className="mt-2 space-y-1.5">
                      <AdaptiveRow
                        title="Research Report"
                        meta="4 agents · Sequential"
                        selected
                        tone="dark"
                      />
                      <AdaptiveRow
                        title="Competitive Research"
                        meta="3 agents · Hierarchical"
                        tone="dark"
                      />
                    </div>
                  </div>

                  <div>
                    <Label color={`${DARK_TEXT}80`}>Domain</Label>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {["General", "Finance", "Healthcare", "Real Estate", "Legal"].map(
                        (d) => (
                          <AdaptiveChip
                            key={d}
                            active={d === "Finance"}
                            tone="dark"
                          >
                            {d}
                          </AdaptiveChip>
                        ),
                      )}
                    </div>
                  </div>

                  <div>
                    <Label color={`${DARK_TEXT}80`}>Topic</Label>
                    <p
                      className="mt-2 border-b pb-3 text-[17px]"
                      style={{
                        color: DARK_TEXT,
                        borderColor: `${DARK_TEXT}25`,
                      }}
                    >
                      AI-powered personalization in luxury retail 2026
                    </p>
                  </div>

                  <button
                    className="group flex w-full items-center justify-between rounded-full px-6 py-3.5 text-[14px] font-semibold transition"
                    style={{ background: LIME, color: DARK }}
                  >
                    <span>Launch crew</span>
                    <span aria-hidden className="transition group-hover:translate-x-1">→</span>
                  </button>
                </div>
              </div>
            </section>

            {/* Right — light glass */}
            <section className="col-span-12 md:col-span-6 md:col-start-7">
              <div
                className="relative overflow-hidden rounded-3xl border p-7 shadow-[0_20px_60px_-10px_rgba(26,24,20,0.12)]"
                style={{
                  borderColor: `${CREAM_TEXT}18`,
                  background: "rgba(253, 250, 242, 0.72)",
                  backdropFilter: "blur(24px) saturate(180%)",
                }}
              >
                <div className="mb-5 flex items-center justify-between">
                  <Label color={`${CREAM_TEXT}aa`}>Live run</Label>
                  <span
                    className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold"
                    style={{
                      background: `${CREAM_TEXT}0f`,
                      color: CREAM_TEXT,
                    }}
                  >
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: "#16a34a" }}
                    />
                    Running
                  </span>
                </div>

                <div className="space-y-2">
                  <AdaptiveAgent
                    role="Researcher"
                    detail="Pulled 14 sources from Google News"
                    state="done"
                    tone="light"
                  />
                  <AdaptiveAgent
                    role="Analyst"
                    detail="Cross-referencing competitive positioning…"
                    state="active"
                    tone="light"
                  />
                  <AdaptiveAgent
                    role="Writer"
                    detail="Queued"
                    state="queued"
                    tone="light"
                  />
                  <AdaptiveAgent
                    role="Validator"
                    detail="Queued"
                    state="queued"
                    tone="light"
                  />
                </div>

                <div
                  className="mt-6 border-t pt-5"
                  style={{ borderColor: `${CREAM_TEXT}15` }}
                >
                  <Label color={`${CREAM_TEXT}aa`}>Elapsed</Label>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span
                      className="text-[56px] leading-none tracking-tight tabular-nums"
                      style={{ fontFamily: "var(--mockup-display)", color: CREAM_TEXT }}
                    >
                      42.1
                    </span>
                    <span className="text-sm" style={{ color: `${CREAM_TEXT}99` }}>
                      seconds
                    </span>
                  </div>
                  <p className="mt-2 text-xs" style={{ color: `${CREAM_TEXT}aa` }}>
                    Median for this workflow:{" "}
                    <span className="font-semibold" style={{ color: CREAM_TEXT }}>
                      38s
                    </span>
                  </p>
                </div>
              </div>
            </section>
          </div>

          <p
            className="mt-24 text-center text-xs"
            style={{ color: `${CREAM_TEXT}66` }}
          >
            Mockup only · Glass v2 Adaptive · delete when done
          </p>
        </div>
      </div>
    </div>
  );
}

function Label({
  children,
  color,
}: {
  children: React.ReactNode;
  color: string;
}) {
  return (
    <p
      className="text-[10px] font-semibold uppercase tracking-[0.22em]"
      style={{ color }}
    >
      {children}
    </p>
  );
}

function AdaptiveRow({
  title,
  meta,
  selected,
  tone,
}: {
  title: string;
  meta: string;
  selected?: boolean;
  tone: "dark" | "light";
}) {
  const isDark = tone === "dark";
  const base = isDark ? DARK_TEXT : CREAM_TEXT;
  return (
    <button
      className="group flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition"
      style={
        selected
          ? {
              borderColor: `${LIME}99`,
              background: `${LIME}14`,
            }
          : {
              borderColor: `${base}18`,
              background: `${base}06`,
            }
      }
    >
      <div>
        <p
          className="text-[15px]"
          style={{ color: selected ? LIME : base }}
        >
          {title}
        </p>
        <p className="mt-0.5 text-[12px]" style={{ color: `${base}aa` }}>
          {meta}
        </p>
      </div>
      {selected ? (
        <span style={{ color: LIME }}>●</span>
      ) : (
        <span style={{ color: `${base}55` }}>→</span>
      )}
    </button>
  );
}

function AdaptiveChip({
  active,
  tone,
  children,
}: {
  active?: boolean;
  tone: "dark" | "light";
  children: React.ReactNode;
}) {
  const isDark = tone === "dark";
  const base = isDark ? DARK_TEXT : CREAM_TEXT;
  return (
    <button
      className="rounded-full border px-3 py-1.5 text-[12px] font-medium transition"
      style={
        active
          ? {
              borderColor: `${LIME}aa`,
              background: `${LIME}1a`,
              color: isDark ? LIME : "#4d7c0f",
            }
          : {
              borderColor: `${base}20`,
              background: "transparent",
              color: `${base}cc`,
            }
      }
    >
      {children}
    </button>
  );
}

function AdaptiveAgent({
  role,
  detail,
  state,
  tone,
}: {
  role: string;
  detail: string;
  state: "queued" | "active" | "done";
  tone: "dark" | "light";
}) {
  const isDark = tone === "dark";
  const base = isDark ? DARK_TEXT : CREAM_TEXT;
  const dotColor =
    state === "active"
      ? "#16a34a"
      : state === "done"
        ? base
        : `${base}40`;
  return (
    <div
      className="flex items-center gap-3 rounded-xl border px-3 py-2.5"
      style={{ borderColor: `${base}12` }}
    >
      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{
          background: dotColor,
          boxShadow: state === "active" ? `0 0 0 4px ${dotColor}28` : undefined,
        }}
      />
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-semibold" style={{ color: base }}>
          {role}
        </p>
        <p className="truncate text-[12px]" style={{ color: `${base}99` }}>
          {detail}
        </p>
      </div>
      <span
        className="text-[10px] font-semibold uppercase tracking-[0.14em]"
        style={{ color: `${base}99` }}
      >
        {state}
      </span>
    </div>
  );
}

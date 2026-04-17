/**
 * Glass v2 — Editorial Light.
 *
 * Contrast strategy: warm cream canvas with dark warm-black text (15:1).
 * Glass is used as ACCENT overlays — a frosted card that sits ON
 * content, not around it — so translucency reads as a design element,
 * not as a readability problem. Single signature accent: rust. Display
 * type is Fraunces (editorial serif) at architectural scale.
 *
 * Delete this file to remove the mockup.
 */

import Link from "next/link";
import { Fraunces, Space_Grotesk } from "next/font/google";

const display = Fraunces({
  subsets: ["latin"],
  weight: ["400", "600"],
  style: ["normal", "italic"],
  variable: "--mockup-display",
});
const body = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--mockup-body",
});

const CREAM = "#f5f1e8";
const INK = "#1a1814";
const RUST = "#b84617";

export default function GlassEditorial() {
  return (
    <div
      className={`${display.variable} ${body.variable} min-h-screen`}
      style={{
        fontFamily: "var(--mockup-body)",
        background: CREAM,
        color: INK,
      }}
    >
      <div className="mx-auto max-w-[1280px] px-8 py-10">
        <nav className="mb-16 flex items-center justify-between text-xs" style={{ color: `${INK}99` }}>
          <Link href="/mockups" className="hover:underline">
            ← Mockups
          </Link>
          <span className="font-semibold uppercase tracking-[0.18em]" style={{ color: RUST }}>
            Glass · Editorial Light
          </span>
        </nav>

        {/* Editorial hero — large serif, drop cap feel, rule below */}
        <header className="mb-20">
          <p className="mb-6 text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: `${INK}aa` }}>
            Multi-agent research desk · Volume IV
          </p>
          <h1
            className="text-[92px] leading-[0.9] tracking-[-0.02em] md:text-[148px]"
            style={{ fontFamily: "var(--mockup-display)", color: INK }}
          >
            A research
            <br />
            <em className="font-normal italic" style={{ color: RUST }}>
              desk{" "}
            </em>
            of four.
          </h1>
          <div className="mt-12 grid grid-cols-12 gap-8">
            <p className="col-span-12 md:col-span-5 md:col-start-8 text-[17px] leading-[1.65]" style={{ color: `${INK}d9` }}>
              Four agents — Researcher, Analyst, Writer, Validator —
              collaborate on one topic, live on a single page. Share links,
              replay scrubs, and PDF exports included.
            </p>
          </div>
        </header>

        {/* Launcher on the left, floating glass "inspector" overlay on the right.
            The glass panel sits OVER content rather than containing it, so
            its translucency is decorative, not obstructing readability. */}
        <div className="relative grid grid-cols-12 gap-10">
          <section className="col-span-12 md:col-span-7">
            <div className="mb-10 border-t-2" style={{ borderColor: INK }}>
              <p
                className="mt-6 text-[12px] font-semibold uppercase tracking-[0.22em]"
                style={{ color: `${INK}aa` }}
              >
                § Launch a crew
              </p>
              <h2
                className="mt-3 text-[44px] leading-[1.02] tracking-tight"
                style={{ fontFamily: "var(--mockup-display)" }}
              >
                Pick a workflow, drop in a topic, press <em className="italic">Launch</em>.
              </h2>
            </div>

            {/* Workflow — editorial list, not a dropdown */}
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: `${INK}aa` }}>
              Workflow
            </p>
            <ul className="mb-10 divide-y-2" style={{ borderColor: INK }}>
              <EditRow title="Research Report" meta="4 agents · Sequential" selected />
              <EditRow title="Competitive Research" meta="3 agents · Hierarchical" />
              <EditRow title="Support Triage" meta="3 agents · Hierarchical" />
              <EditRow title="Sales Qualification" meta="2 agents · Sequential" />
            </ul>

            <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: `${INK}aa` }}>
              Domain
            </p>
            <div className="mb-10 flex flex-wrap gap-1.5">
              {["General", "Finance", "Healthcare", "Real Estate", "Legal", "Education"].map((d) => (
                <EditChip key={d} active={d === "Finance"}>
                  {d}
                </EditChip>
              ))}
            </div>

            <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: `${INK}aa` }}>
              Topic
            </p>
            <p
              className="border-b-2 pb-4 text-[24px] leading-tight"
              style={{ fontFamily: "var(--mockup-display)", borderColor: INK, color: INK }}
            >
              AI-powered personalization in luxury retail 2026
            </p>

            <button
              className="mt-10 inline-flex items-center gap-3 rounded-none border-2 px-8 py-4 text-[14px] font-semibold uppercase tracking-[0.22em] transition hover:bg-black/5"
              style={{ borderColor: INK, color: INK }}
            >
              Launch crew
              <span aria-hidden>→</span>
            </button>
          </section>

          {/* Floating glass inspector — this is where translucency earns
              its keep: the bg below (cream + the editorial body text)
              shows through softly, but the inspector's own text is on a
              nearly-opaque white frost, so contrast stays strong. */}
          <aside className="col-span-12 md:col-span-5">
            <div className="sticky top-8">
              <div
                className="overflow-hidden rounded-3xl border p-7 shadow-[0_20px_60px_-10px_rgba(26,24,20,0.15)]"
                style={{
                  borderColor: `${INK}22`,
                  background: "rgba(253, 250, 242, 0.72)",
                  backdropFilter: "blur(24px) saturate(180%)",
                }}
              >
                <div className="mb-5 flex items-center justify-between">
                  <span
                    className="text-[10px] font-semibold uppercase tracking-[0.22em]"
                    style={{ color: `${INK}aa` }}
                  >
                    Live run
                  </span>
                  <span
                    className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold"
                    style={{
                      background: "rgba(184, 70, 23, 0.12)",
                      color: RUST,
                    }}
                  >
                    <span className="h-1.5 w-1.5 rounded-full" style={{ background: RUST }} />
                    Running
                  </span>
                </div>

                <div className="space-y-2">
                  <EditAgent role="Researcher" detail="Pulled 14 sources" state="done" />
                  <EditAgent role="Analyst" detail="Cross-referencing competitors…" state="active" />
                  <EditAgent role="Writer" detail="Queued" state="queued" />
                  <EditAgent role="Validator" detail="Queued" state="queued" />
                </div>

                <div className="mt-7 border-t pt-5" style={{ borderColor: `${INK}15` }}>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: `${INK}aa` }}>
                    Elapsed
                  </p>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span
                      className="text-[56px] leading-none tracking-tight tabular-nums"
                      style={{ fontFamily: "var(--mockup-display)" }}
                    >
                      42.1
                    </span>
                    <span className="text-sm" style={{ color: `${INK}99` }}>
                      seconds
                    </span>
                  </div>
                  <p className="mt-2 text-xs" style={{ color: `${INK}aa` }}>
                    Median for this workflow:{" "}
                    <span className="font-semibold" style={{ color: INK }}>
                      38s
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </aside>
        </div>

        <p className="mt-20 text-center text-xs" style={{ color: `${INK}66` }}>
          Mockup only · Glass v2 Editorial Light · delete when done
        </p>
      </div>
    </div>
  );
}

function EditRow({
  title,
  meta,
  selected,
}: {
  title: string;
  meta: string;
  selected?: boolean;
}) {
  return (
    <li
      className={["flex items-baseline justify-between py-5", selected ? "" : ""].join(" ")}
      style={{ borderColor: INK }}
    >
      <div className="flex items-baseline gap-5">
        <span
          className="w-8 text-[11px] font-semibold uppercase tracking-[0.22em]"
          style={{ color: selected ? RUST : `${INK}99` }}
        >
          {selected ? "◉" : "○"}
        </span>
        <div>
          <p
            className="text-[24px] leading-tight"
            style={{
              fontFamily: "var(--mockup-display)",
              color: selected ? RUST : INK,
            }}
          >
            {title}
          </p>
          <p className="mt-0.5 text-[13px]" style={{ color: `${INK}99` }}>
            {meta}
          </p>
        </div>
      </div>
    </li>
  );
}

function EditChip({
  active,
  children,
}: {
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      className="rounded-full border px-3.5 py-1.5 text-[12px] font-medium transition"
      style={
        active
          ? { borderColor: RUST, background: `${RUST}12`, color: RUST }
          : { borderColor: `${INK}25`, background: "transparent", color: `${INK}cc` }
      }
    >
      {children}
    </button>
  );
}

function EditAgent({
  role,
  detail,
  state,
}: {
  role: string;
  detail: string;
  state: "queued" | "active" | "done";
}) {
  const color =
    state === "active" ? RUST : state === "done" ? "#1a1814" : `${INK}66`;
  return (
    <div className="flex items-center gap-3 rounded-xl border px-3 py-2.5" style={{ borderColor: `${INK}12` }}>
      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{
          background: color,
          boxShadow: state === "active" ? `0 0 0 4px ${RUST}28` : undefined,
        }}
      />
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-semibold" style={{ color: INK }}>
          {role}
        </p>
        <p className="truncate text-[12px]" style={{ color: `${INK}99` }}>
          {detail}
        </p>
      </div>
      <span className="text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color: `${INK}99` }}>
        {state}
      </span>
    </div>
  );
}

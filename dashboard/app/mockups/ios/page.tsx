/**
 * Mockup — iOS HIG (Apple Human Interface Guidelines).
 *
 * Signatures: SF-style typography, system gray palette, grouped insets,
 * segmented controls, disciplined hierarchy, minimal shadow, dividers
 * instead of borders, blue (indigo) accent for action. Self-contained —
 * delete the file to remove.
 */

import Link from "next/link";

const SF =
  "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', sans-serif";

export default function IOSMockup() {
  return (
    <div
      className="min-h-screen bg-[#f2f2f7] text-[#1c1c1e]"
      style={{ fontFamily: SF }}
    >
      <div className="mx-auto max-w-3xl px-5 py-10">
        <nav className="mb-8 flex items-center justify-between text-[13px]">
          <Link href="/mockups" className="text-[#007aff]">
            ‹ Mockups
          </Link>
          <span className="font-semibold">AI Agent Team</span>
          <span className="w-12 text-right text-[#8e8e93]">v4.2</span>
        </nav>

        <header className="mb-6 px-2">
          <h1 className="text-[34px] font-bold leading-tight tracking-tight">
            Launch a crew
          </h1>
          <p className="mt-1 text-[15px] leading-snug text-[#3c3c43]/80">
            Pick a pre-built crew, drop in a topic, and watch the team work.
          </p>
        </header>

        {/* Grouped inset list — quintessential iOS */}
        <section className="mb-4">
          <p className="mb-1.5 px-4 text-[13px] font-normal uppercase tracking-wide text-[#6c6c70]">
            Workflow
          </p>
          <div className="overflow-hidden rounded-xl bg-white">
            <Row value="Research Report" detail="4 agents · Sequential" selected />
            <Row value="Competitive Research" detail="3 agents · Hierarchical" />
            <Row value="Support Triage" detail="3 agents · Hierarchical" />
            <Row value="Sales Qualification" detail="2 agents · Sequential" last />
          </div>
        </section>

        <section className="mb-4">
          <p className="mb-1.5 px-4 text-[13px] font-normal uppercase tracking-wide text-[#6c6c70]">
            Domain
          </p>
          <div className="overflow-hidden rounded-xl bg-white">
            <Row value="Finance" selected />
            <Row value="Healthcare" />
            <Row value="Real Estate" />
            <Row value="Legal" />
            <Row value="General" last />
          </div>
        </section>

        <section className="mb-8">
          <p className="mb-1.5 px-4 text-[13px] font-normal uppercase tracking-wide text-[#6c6c70]">
            Topic
          </p>
          <div className="overflow-hidden rounded-xl bg-white">
            <div className="px-4 py-3 text-[17px]">
              AI-powered personalization in luxury retail 2026
            </div>
          </div>
          <p className="mt-1.5 px-4 text-[12px] text-[#6c6c70]">
            Used as the task brief for every agent in the crew.
          </p>
        </section>

        <button className="mb-10 w-full rounded-xl bg-[#007aff] py-3.5 text-[17px] font-semibold text-white active:opacity-80">
          Launch crew
        </button>

        {/* Live section mimicking a Settings-style summary */}
        <section>
          <p className="mb-1.5 px-4 text-[13px] font-normal uppercase tracking-wide text-[#6c6c70]">
            Latest run
          </p>
          <div className="overflow-hidden rounded-xl bg-white">
            <SummaryRow
              role="Researcher"
              detail="Pulled 14 sources from Google News"
              status="Done"
              statusColor="#34c759"
            />
            <SummaryRow
              role="Analyst"
              detail="Cross-referencing competitive positioning…"
              status="Active"
              statusColor="#007aff"
            />
            <SummaryRow role="Writer" detail="—" status="Queued" statusColor="#8e8e93" />
            <SummaryRow
              role="Validator"
              detail="—"
              status="Queued"
              statusColor="#8e8e93"
              last
            />
          </div>
        </section>

        <p className="mt-12 text-center text-[11px] text-[#8e8e93]">
          Mockup only · iOS HIG · delete when done
        </p>
      </div>
    </div>
  );
}

function Row({
  value,
  detail,
  selected,
  last,
}: {
  value: string;
  detail?: string;
  selected?: boolean;
  last?: boolean;
}) {
  return (
    <div
      className={[
        "flex items-center justify-between px-4 py-3",
        last ? "" : "border-b border-[#d1d1d6]/60",
      ].join(" ")}
    >
      <div>
        <p className="text-[17px] leading-tight">{value}</p>
        {detail ? (
          <p className="mt-0.5 text-[13px] text-[#6c6c70]">{detail}</p>
        ) : null}
      </div>
      {selected ? (
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#007aff"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : (
        <svg
          width="8"
          height="13"
          viewBox="0 0 8 13"
          aria-hidden
          className="text-[#c7c7cc]"
        >
          <path
            d="M1 1l6 5.5L1 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </div>
  );
}

function SummaryRow({
  role,
  detail,
  status,
  statusColor,
  last,
}: {
  role: string;
  detail: string;
  status: string;
  statusColor: string;
  last?: boolean;
}) {
  return (
    <div
      className={[
        "flex items-center justify-between px-4 py-3",
        last ? "" : "border-b border-[#d1d1d6]/60",
      ].join(" ")}
    >
      <div className="min-w-0">
        <p className="text-[15px] font-semibold">{role}</p>
        <p className="truncate text-[13px] text-[#6c6c70]">{detail}</p>
      </div>
      <span
        className="shrink-0 rounded-full px-2.5 py-0.5 text-[12px] font-semibold text-white"
        style={{ backgroundColor: statusColor }}
      >
        {status}
      </span>
    </div>
  );
}

import Link from "next/link";

/**
 * Throwaway index for v4.2 UI theme comparison (delete after the user picks).
 *
 * Round 1 (top): three baseline aesthetics — Liquid Glass, iOS HIG, Pro Max.
 * Round 2 (bottom): three Liquid Glass iterations addressing contrast,
 * typography, and colour issues from the original Glass critique.
 */

const ROUND_1 = [
  {
    slug: "glass",
    title: "Liquid Glass (v1)",
    tagline: "Apple 2025 — translucency + vibrancy",
    blurb:
      "Frosted backdrops, specular highlights, blurred rainbow gradient. Baseline — pretty but fails WCAG contrast in several spots.",
  },
  {
    slug: "ios",
    title: "iOS HIG",
    tagline: "Apple Human Interface Guidelines",
    blurb:
      "SF-style type, disciplined hierarchy, adaptive colors. Credible + restrained, not flashy.",
  },
  {
    slug: "pro-max",
    title: "UI-UX Pro Max",
    tagline: "Refactoring UI — tightened shadcn",
    blurb:
      "Same system we have now, but with stricter scales for spacing, type, and color. Low risk, big gain.",
  },
];

const ROUND_2 = [
  {
    slug: "glass-v2-dark",
    title: "Glass v2 · Dark Mono",
    tagline: "Warm near-black + single amber bloom",
    blurb:
      "Dark canvas means dark-on-dark frost always passes contrast. Instrument Serif display at 128px, Space Grotesk body. One signature accent: amber.",
  },
  {
    slug: "glass-v2-editorial",
    title: "Glass v2 · Editorial Light",
    tagline: "Cream paper + rust ink + Fraunces",
    blurb:
      "Editorial serif treatment. Glass is a floating inspector panel on top of content, not a content container — translucency stays decorative. 15:1 text contrast.",
  },
  {
    slug: "glass-v2-adaptive",
    title: "Glass v2 · Adaptive (split)",
    tagline: "Dark + light meeting at a typographic seam",
    blurb:
      "Two halves, two glass treatments. Signature moment: one headline that splits across the seam and inverts. Single accent: electric lime.",
  },
];

export default function MockupsIndex() {
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-12">
      <header className="mb-10">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Temporary — delete after decision
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Theme mockups
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600 dark:text-zinc-400">
          Same content, three aesthetics per round. Round 1 is the original
          three-way comparison. Round 2 is three Liquid Glass iterations that
          fix the readability + "AI gradient" issues from v1.
        </p>
      </header>

      <section className="mb-12">
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
            Round 1 · Baseline comparison
          </h2>
          <span className="text-xs text-zinc-400">3 aesthetics</span>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {ROUND_1.map((t) => (
            <Card key={t.slug} theme={t} />
          ))}
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
            Round 2 · Liquid Glass iterations
          </h2>
          <span className="text-xs text-zinc-400">
            Premium fonts · contrast-safe · single-accent palettes
          </span>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {ROUND_2.map((t) => (
            <Card key={t.slug} theme={t} accent />
          ))}
        </div>
      </section>

      <footer className="mt-16 rounded-lg border border-zinc-200 bg-zinc-50 p-5 text-sm text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-400">
        <p className="font-semibold text-zinc-900 dark:text-zinc-50">
          Critique of the original Glass (v1)
        </p>
        <ul className="mt-2 list-inside list-disc space-y-1">
          <li>
            Typography ~4/10 — default system-ui, hero:body ratio only ~3:1
            (goal is 10:1+ per Awwwards rubric).
          </li>
          <li>
            Color ~3/10 — purple→pink→cyan gradient is the textbook "AI
            aesthetic" red flag; white text drops below 4.5:1 on bright areas.
          </li>
          <li>
            Composition ~5/10 — centered + symmetric, no asymmetric tension,
            no bleed, no signature moment.
          </li>
          <li>
            Details ~5/10 — everything <code>rounded-full</code> or{" "}
            <code>rounded-2xl</code> (the "rounded everything" AI tell).
          </li>
        </ul>
        <p className="mt-3">
          Round 2 variants each fix the contrast problem via a different
          structural choice — pick the one that feels right and the other
          five mockups get deleted.
        </p>
      </footer>
    </main>
  );
}

function Card({
  theme,
  accent,
}: {
  theme: { slug: string; title: string; tagline: string; blurb: string };
  accent?: boolean;
}) {
  return (
    <Link
      href={`/mockups/${theme.slug}`}
      className={[
        "group flex flex-col gap-2 rounded-xl border bg-white p-5 shadow-sm transition-shadow hover:shadow-md",
        accent
          ? "border-indigo-200 dark:border-indigo-500/40 dark:bg-zinc-900"
          : "border-zinc-200 dark:border-zinc-800 dark:bg-zinc-900",
      ].join(" ")}
    >
      <span
        className={[
          "text-xs font-semibold uppercase tracking-wider",
          accent ? "text-indigo-600 dark:text-indigo-400" : "text-zinc-500",
        ].join(" ")}
      >
        {theme.tagline}
      </span>
      <h3 className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        {theme.title}
      </h3>
      <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
        {theme.blurb}
      </p>
      <span
        className={[
          "mt-auto pt-2 text-xs font-medium group-hover:underline",
          accent ? "text-indigo-600 dark:text-indigo-400" : "text-zinc-700 dark:text-zinc-300",
        ].join(" ")}
      >
        Open mockup →
      </span>
    </Link>
  );
}

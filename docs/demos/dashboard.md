# Dashboard demo — Graph Team View (v4.1)

Ten-minute, screen-share-ready walkthrough of the agent dashboard. Covers
every slice in Phase 4.1 (29a–29e): topology, live animation, transcript,
share-page scrubber, polish.

## Prereqs

- `docker compose -f docker-compose.dev.yml up -d` (qdrant + agents-api + chainlit)
- `cd dashboard && npm run dev` (Next.js on :3000 or :3061 in Docker)
- `DEMO_MODE=true` in the backend `.env.local` so the deterministic FakeLLM
  drives the crew — no API keys needed.

## Flow

### 1 · Launch a run

1. Open the dashboard at `http://localhost:3000`.
2. Pick the **research_report** workflow, leave the domain on `finance`,
   enter a topic like "AI in retail 2026".
3. Click **Launch**. The workflow description "expands" into the graph
   header via a framer-motion `layoutId` shared-element transition.
   (Skipped if `prefers-reduced-motion` is on — no layout ID swap.)

### 2 · Watch the graph animate (slice 29a + 29b)

- Four agent nodes, three sequential edges — the topology is derived
  from the registry, not hand-authored.
- Active agent pulses (indigo halo). Source→target edge shimmers during
  the 3s around the handoff; a small packet dot slides along the bezier
  in the first 600ms.
- Waiting agents go amber; failed agents shake once.
- `prefers-reduced-motion` kills every keyframe + hides the packet dot;
  state chips and halos still update so the reducer is observable.

### 3 · Read the transcript (slice 29c)

- Right-hand pane shows one collapsible section per agent.
- The currently-active section auto-expands; others stay closed until
  clicked.
- An IntersectionObserver sentinel auto-scrolls to the latest entry.
  Scroll up and the sentinel leaves the viewport — auto-scroll pauses
  until you return to the bottom.
- "Copy" on a section writes only that agent's transcript to the
  clipboard.

### 4 · Keyboard navigation (slice 29e)

- Tab through the top-nav, the view toggle, the graph, then the
  transcript. Each agent node is a `role="button"` with
  `aria-label="Agent … — state. Press Enter to jump to transcript."`.
- **Enter** on a focused node dispatches a `graph:focus-role` event;
  TranscriptPane expands and scrolls the matching section into view.
- axe-core (WCAG 2 A / AA) comes up clean on `/runs/[id]` —
  verified in CI via `dashboard/e2e/graph-a11y.spec.ts`.

### 5 · Share + replay (slice 29d)

1. When the run completes, click **Copy Share Link** (HMAC-signed,
   7-day TTL).
2. Open the share link in a private window.
3. The share page is the same dual-pane layout *plus* a scrubber:
   - Drag the slider to 0: the graph rewinds to all-queued.
   - Drag to the end: final state.
   - Press **Space**: auto-advance at ts-delta speed (capped at 2×
     real-time).
   - If any event was `state=failed`, a "Jump to failure" button
     appears to jump straight to the failing frame.
4. `GET /share/{token}?format=json` powers the replay; the original
   HTML variant of `/share/{token}` is untouched for curl + PDF
   consumers.

## Manual Lighthouse pass

Run Lighthouse in Chrome DevTools (`Ctrl+Shift+I → Lighthouse`) on
`/runs/[id]` and `/share/[token]`:

- Accessibility: ≥ 95
- Performance: ≥ 85 on local dev, higher in prod build
- Best Practices: ≥ 90
- SEO: not a goal for authenticated views

axe-core in `dashboard/e2e/graph-a11y.spec.ts` is the authoritative
regression gate; Lighthouse is a spot check for each demo rehearsal.

## Troubleshooting

- **Graph is empty** — backend `/workflows` endpoint failed; check the
  header error banner and `docker compose logs agents-api`.
- **SSE stalls** — the rate limiter's storage is in-memory; restart the
  backend container.
- **Share link 410** — the 7-day TTL elapsed; mint a fresh one via
  `POST /share/mint` with the task_id.
- **Animations are too aggressive** — flip your OS to "Reduce motion"
  (macOS: System Settings → Accessibility → Display) or set
  `matchMedia('(prefers-reduced-motion: reduce)')` via DevTools
  emulation.

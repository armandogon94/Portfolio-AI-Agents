# Verticals Demo — Content & Real Estate (5 minutes)

**Goal:** Prospect sees two vertical-specific workflows — a full editorial
pipeline that drafts a blog post, and a Comparative Market Analysis (CMA) that
produces a defensible value range for a property.

**Prereqs:**

```bash
docker compose -f docker-compose.dev.yml up -d
export DEMO_MODE=true    # slice 28; skip until it lands
# Seed the real_estate domain so comps + market have RAG context:
uv run python scripts/seed_rag.py --domain real_estate
```

---

## Act 1 — Content Pipeline (2.5 minutes)

**Setup line:** *"Five agents, one sequential pipeline: researcher finds
sources, outliner plans the structure, writer drafts, editor polishes, and
the SEO optimizer produces metadata. Think of it as a compressed editorial
team."*

1. Launcher:
   - Workflow: `content_pipeline`
   - Domain: `general` (or the prospect's vertical for relevance)
   - Topic: *"How AI agents are changing customer support in 2026"*
2. Click **Launch**.
3. On the run page, point at the cards marching across columns one at a
   time — this is the sequential workflow that contrasts with the parallel
   ones in the other demos.
4. When the SEO optimizer finishes, read the JSON output aloud:
   - `title` (≤60 chars), `meta_description` (≤155), `slug`,
     `readability_score`, and 3-5 `seo_suggestions`.

**Close:** *"That's a publish-ready post plus metadata in one launch. Swap
the writer for an industry-specific copywriter and you have a vertical
content engine."*

---

## Act 2 — Real Estate CMA (2.5 minutes)

**Setup line:** *"A comparative market analysis. Two agents run in parallel —
the comps gatherer pulls recent sales, the market analyst pulls local
trends — then an appraiser produces a defensible value range, and a report
writer assembles the client-facing CMA."*

1. Launcher:
   - Workflow: `real_estate_cma`
   - Domain: `real_estate`
   - Topic: *"123 Main St, Austin TX 78704, 3 bed 2 bath, 1850 sqft, 1994"*
2. Click **Launch**.
3. Point at the two researchers lit simultaneously — that's the parallel
   group. The appraiser is in Waiting with *"waiting on parallel group"*
   from the state bus telegraph.
4. When the appraiser finishes, read the JSON:
   - `estimated_value_range.low`, `.high`, `confidence`, and the
     `disclaimer` that labels this as a computer-generated estimate,
     **not** a licensed appraisal.
5. When the CMA report is done, scroll through the markdown sections:
   Summary, Comparables (with source URLs), Market, Estimated Value,
   Disclaimer.

**Close:** *"This is read-only by design. There's no 'target price' input —
a user can't bias the estimate through the API. If your industry needs a
biased rubric, that's a one-file change in `src/workflows/real_estate_cma.py`."*

---

## Q&A cheat-sheet

| Question | Answer |
|----------|--------|
| *"Does the content pipeline respect voice guidelines?"* | The editor's prompt explicitly "preserves author voice — minimal rewrites." For a hard-voice-lock, add a tone prompt to the editor's backstory and a regression test fixture. |
| *"Where does the CMA's data come from?"* | Web search + RAG over the `real_estate` domain documents you seed. Swap in MLS via a new tool in `src/tools/` and re-register; no workflow change needed. |
| *"Why is CMA read-only?"* | Security (DEC-18 workflow-as-code + slice-25 rubric guard). A CMA that accepts a `target_price` input is a bias vector — we reject it at the schema level, enforced by a unit test. |
| *"SEO readability score source?"* | Flesch reading-ease approximation from the optimizer agent. Not authoritative — replace with a calculated score via a custom tool if legal needs it. |
| *"Can I run both at once?"* | Yes — two `POST /crew/run` calls return two task_ids; the dashboard history shows both; each has its own live-view URL. |

---

## Troubleshooting

- **Outliner hallucinates sections the research didn't cover.** The outliner
  prompt says "never invent facts" but qwen3:8b sometimes drifts. Tighten by
  passing the research output verbatim via `{prior_context}` or switch to
  Anthropic.
- **CMA estimate range is absurdly wide.** Confidence will be low in that
  case. Check the comps — if they're missing source URLs the market
  analyst's narrative was probably thin. Re-seed the RAG corpus.
- **SEO JSON occasionally malformed.** The seo_optimizer task's
  `expected_output` contract requests JSON; if the LLM emits prose, a
  downstream consumer will fail. Slice 27's PDF export + slice 28's
  fake LLM both sidestep this for pitches.

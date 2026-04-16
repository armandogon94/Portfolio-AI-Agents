# Sales Demo — 5-minute pitch script

**Goal:** Prospect watches two workflows: a lead qualifier that scores a real
company, and an SDR outreach generator that drafts three email variants in
parallel and picks the best one.

**Stack to have running** (in this order):

```bash
docker compose -f docker-compose.dev.yml up -d            # qdrant, api, chainlit, dashboard
export DEMO_MODE=true                                     # swap live LLM for deterministic fixtures (slice 28)
```

> Until slice 28 lands, skip the `DEMO_MODE` step. The demo still runs
> with real Ollama but is slower and less reproducible.

Open **two** browser tabs:

1. `http://localhost:3061` — the launcher
2. `http://localhost:3061/runs` — the history (optional but useful as a
   closer)

---

## Act 1 — Lead Qualifier (2 minutes)

**Setup line:** *"Let me show you the first of two sales workflows. It takes a
prospect name, researches them, scores them against your ICP rubric, and drafts
a one-page brief for your AE."*

1. On the launcher:
   - Workflow: `lead_qualifier`
   - Domain: `general` (or vertical if relevant)
   - Topic: `Acme Corp` (substitute the prospect's own customer for maximum
     effect)
2. Click **Launch**. The page navigates to `/runs/:id`.
3. Point at the kanban columns as the researcher card moves **Queued → Active**.
4. Call out the **rubric** — it lives in `src/workflows/lead_qualifier.py`
   as `SCORING_RUBRIC`, not in a prompt. That's the tampering-guard: the
   same research produces the same score.
5. When the scorer card finishes, point at the JSON output — explicit
   sub-scores, weights, evidence URLs.
6. When the report writer card finishes, read the executive summary aloud.

**Close the act:** *"That brief is now something your AE can open in their
inbox before the first call."*

---

## Act 2 — SDR Outreach (3 minutes)

**Setup line:** *"Now watch three writers work in parallel. The system
researches the persona, drafts a formal, casual, and provocative variant
simultaneously, then picks the winner."*

1. On the launcher:
   - Workflow: `sdr_outreach`
   - Topic: `CTO at Acme Corp, ex-Stripe, posts about observability`
     (the more specific, the better the persona sketch)
2. Click **Launch**.
3. On the run page, call out the **three Active cards lit at once** — that's
   the parallelism demo. Point at the Waiting column: `tone_checker` is
   already telegraphed as blocked on the drafting group.
4. When drafts complete, the tone checker runs; read the winner's
   justification aloud.

**Close the act:** *"Three drafts, one pick, all on your laptop. No API
costs, verifiable rubric, and every stage is observable."*

---

## Q&A cheat-sheet

| Question | Answer |
|----------|--------|
| *"Can I plug in my own ICP rubric?"* | Yes — it's a Python module constant. A PR to `src/workflows/lead_qualifier.py::SCORING_RUBRIC` ships a new version. Deliberately not user-input; keeps scoring reproducible. |
| *"What model is this?"* | Local Ollama in dev (qwen3:8b), Anthropic Claude in prod. `LLM_PROVIDER` flips between them. |
| *"Can it call the lead?"* | Not today. Voice receptionist lands in slice 26 (Twilio trial, opt-in, TCPA-guarded). |
| *"Export?"* | Slice 27: share link (HMAC-signed, 7-day TTL) + PDF. |
| *"How do I add a 4th variant?"* | Add a `copywriter_witty` agent in `agents.yaml`, a `draft_witty` task in `tasks.yaml`, and include both in `sdr_outreach.py`'s `agent_roles` + `task_names` + `parallel_tasks`. |

---

## Troubleshooting

- **Cards stuck in Queued.** The Ollama container didn't come up. `docker
  compose logs agents-api | tail -20` — usually a missing `OLLAMA_BASE_URL`
  or model-not-pulled.
- **Three drafts but only one agent card lit.** The task_id didn't reach
  the state bus. Restart the API container.
- **Dashboard shows "Connection interrupted."** Tab was backgrounded for
  longer than uvicorn's keep-alive. EventSource auto-reconnects; click
  away and back.

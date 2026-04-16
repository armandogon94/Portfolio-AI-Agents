# Support & Ops Demo — 5-minute pitch script

**Goal:** Prospect watches two workflows that show hierarchy and parallelism
respectively — a support triage manager delegating to three specialists, and a
meeting prep flow with two researchers running concurrently.

**Prereqs:**

```bash
docker compose -f docker-compose.dev.yml up -d
export DEMO_MODE=true    # slice 28; skip until it lands
```

Open **two** tabs:
1. `http://localhost:3061` — launcher
2. `http://localhost:3061/runs` — history (for the closer)

---

## Act 1 — Support Triage (2.5 minutes)

**Setup line:** *"First workflow: a hierarchical crew. A triage manager
delegates to three specialists — a KB searcher, a sentiment analyst, and a
response writer. Watch the manager card in the Active column while the three
specialists do the real work."*

1. Launcher:
   - Workflow: `support_triage`
   - Domain: `general` (or `healthcare` / `finance` for vertical KB)
   - Topic: paste a real-ish ticket, e.g.
     > "My invoice for March is double what it usually is and support said
     >  I'd hear back in 24h — that was 5 days ago. Legal has been looped
     >  in. — Jane Doe, CFO at Acme."
2. Click **Launch**.
3. On the run page, call out the hierarchy:
   - The **triage_manager** runs continuously (this is the manager agent;
     CrewAI moves it through Active during delegation).
   - The three specialists appear in **Active** one-after-another as the
     manager delegates.
4. When the crew finishes, read the JSON output:
   - `urgency: "high"`, `escalation_flags: ["legal mention"]`,
     `category: "billing"`, and the stitched `suggested_response`.

**Close:** *"Notice the agents weren't told the order by the prompt — the
manager chose who to call. That's the hierarchical process."*

---

## Act 2 — Meeting Prep (2.5 minutes)

**Setup line:** *"Second workflow: parallel research. The attendee researcher
and the topic researcher run simultaneously; the agenda writer waits for both;
then talking points writer does the final pass."*

1. Launcher:
   - Workflow: `meeting_prep`
   - Topic: e.g.
     > "30-min call Thursday with Jane Doe (CFO, Acme) and Bob Chen (CTO, Acme)
     >  about our Q2 renewal and their move to multi-region."
2. Click **Launch**.
3. On the run page, the **moneyshot**:
   - *Two* Active cards at once — `attendee_researcher` and
     `topic_researcher` both running.
   - `agenda_writer` and `talking_points_writer` in the **Waiting** column
     with *"waiting on parallel group"* — that's the state bus telegraphing
     dependencies from build time.
4. When the researchers finish, agenda_writer moves to Active, then done,
   then talking_points_writer.

**Close:** *"That's not faked concurrency — it's CrewAI's `async_execution` at
the task level. Same pattern scales to 5-10 parallel researchers if your
workflow needs it."*

---

## Q&A cheat-sheet

| Question | Answer |
|----------|--------|
| *"Why hierarchical for triage but parallel for meeting prep?"* | Triage has a single answer the manager must *decide* (urgency, category). Meeting prep has two independent information gathers that naturally fan in. DEC-19 keeps delegation opt-in per workflow so neither pays for the other's overhead. |
| *"What's the waiting telegraph?"* | Slice 22's state bus helper emits `waiting_on_agent` events at build time for tasks downstream of a parallel group. The dashboard renders them in the Waiting column before the work starts so prospects see the dependency. |
| *"Does the triage manager route to arbitrary tools?"* | No — it can only delegate to the three specialists declared in `agent_roles`. That's a safety property: tools aren't the manager's; the workers own their own tool lists. |
| *"Can I plug in Zendesk?"* | Not today. You'd add an `ingest_service`-style integration and POST tickets into `POST /crew/run workflow=support_triage`. |

---

## Troubleshooting

- **Manager stuck in Active forever.** The `llm` call to choose the next
  delegate is slow with qwen3:8b. Switch to Anthropic (`LLM_PROVIDER=anthropic`)
  for demos — the manager's planning step is the bottleneck.
- **Only one researcher visible.** If both attendee and topic researchers need
  Qdrant (they do via `document_search`), Qdrant may be single-threaded under
  concurrent search. Watch `docker compose logs qdrant` — you'll see sequential
  search calls but both agent cards still light in the dashboard because each
  agent's step_callback fires independently.
- **Empty KB snippets.** The `kb_searcher` needs content in the Qdrant
  collection. Run `scripts/seed_rag.py --domain healthcare` (or your domain)
  first.

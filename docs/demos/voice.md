# Voice Demo — Twilio-trial Receptionist (slice-26)

**⚠️ TCPA notice (US).** Outbound automated/pre-recorded calls to consumers
without prior express written consent can trigger statutory damages of
**$500–$1,500 per call**. This demo is **for portfolio purposes only**.
Only call numbers you own or have documented written consent to call
(your cell, a test line you operate, a friend who agreed in writing).
The system **refuses** to dial numbers that aren't on the
`TWILIO_VERIFIED_TO_NUMBERS` whitelist — keep the list minimal.

---

## 15-minute first-call setup

### 1. Sign up for Twilio trial (5 min)

- Create a free trial at <https://www.twilio.com/try-twilio>
- Verify your cell phone via SMS — this auto-adds it to the trial's
  verified-numbers list on the Twilio side (separate from our `TWILIO_VERIFIED_TO_NUMBERS` env).
- Copy your **Account SID**, **Auth Token**, and claim a **trial phone
  number** (US long code, ~$1.15/mo out of the $15.50 credit).

### 2. Expose your local API via ngrok (2 min)

The Twilio cloud needs a public URL to POST TwiML webhooks to.

```bash
# In a separate terminal:
ngrok http 8060
```

ngrok prints something like `https://<random>.ngrok-free.app`. Copy it.

### 3. Configure the app (2 min)

Add to `.env.local` (NOT committed — `.gitignore` covers it):

```bash
VOICE_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1YOURTRIALNUMBER          # the number Twilio gave you
TWILIO_WEBHOOK_BASE=https://<your>.ngrok-free.app
TWILIO_VERIFIED_TO_NUMBERS=["+1YOURCELL"]     # JSON list; add your own number first
```

Restart the API so pydantic-settings picks them up:

```bash
docker compose -f docker-compose.dev.yml restart agents-api
```

### 4. Dry-run against the mock (1 min)

```bash
uv run pytest tests/unit/test_voice_tool.py tests/unit/test_twiml_webhook.py
```

All 8 unit tests should pass without any network calls.

### 5. Place a real call (5 min)

```bash
curl -X POST http://localhost:8060/crew/run \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Hi, this is Armando calling to confirm a 7pm reservation for 4 at Luigi's",
    "workflow": "receptionist",
    "voice": {"to": "+1YOURCELL", "max_turns": 4}
  }'
```

Your phone should ring within a few seconds. When you pick up, the agent
will speak its opening line, then `<Gather>` waits for your reply.

Watch the run on the dashboard:

```
http://localhost:3061/runs/<task_id_from_the_response>
```

### 6. Hang up, read the summary

The dashboard's run page shows the kanban columns; once the crew
finishes, the summary_agent's post-call report lands in the run's
final output (via the `_execute_crew` path; share link in slice 27).

---

## Troubleshooting

- **"Voice features are disabled."** `VOICE_ENABLED` is still false. Edit
  `.env.local` and restart the `agents-api` container.
- **"Refusing to dial +1xxx — not in TWILIO_VERIFIED_TO_NUMBERS."** The
  whitelist is empty or doesn't include the target. Add to the JSON list
  in `.env.local` and restart.
- **Twilio webhook returns 403.** ngrok URL or auth token mismatched.
  Double-check `TWILIO_WEBHOOK_BASE` equals the current ngrok URL, and
  that `TWILIO_AUTH_TOKEN` matches the Twilio console.
- **Trial greeting plays before the agent.** That's Twilio's trial-account
  announcement — unavoidable on trial tier. Upgrade to a paid account or
  accept the demo caveat.
- **Webhook 500s.** Check `docker compose logs agents-api`. Common culprit:
  `TWILIO_WEBHOOK_BASE` missing the `https://` prefix.

---

## Safety checklist before each demo

- [ ] Only the phone numbers you genuinely control are in
      `TWILIO_VERIFIED_TO_NUMBERS`.
- [ ] `max_turns ≤ 6` and `max_duration_s ≤ 120` at the request level.
- [ ] You've told the person being called that the call is automated
      and obtained their verbal + written consent.
- [ ] ngrok URL not embedded in any PR, screenshot, or Slack message
      (rotate the Twilio auth token if it is).

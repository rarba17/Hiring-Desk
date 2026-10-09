# Autonomous Hiring Worker

NL instruction -> screen resumes, schedule panel interviews, send confirmations, update ATS. Verified end-to-end over FastAPI + LangGraph + OpenAI.

## Status
| Step | State |
| ---- | ----- |
| Project init | done |
| ATS mock | done |
| Resumes / calendars | done |
| Planner / screener | done |
| Scheduler | done |
| Verifier | done |
| LangGraph supervisor | done |
| Hiring API | done |
| Docker + demo | done |

## Run
```bash
cp .env.example .env   # optional OPENAI_API_KEY; rule-based scoring fallback without it
pip install -r requirements.txt
uvicorn app.api.main:app --reload
# docs: http://localhost:8000/docs
# or: docker compose up --build
```

Try:
```bash
curl -X POST localhost:8000/hiring/tasks -H 'Content-Type: application/json' \
  -d '{"goal":"Schedule interviews for the top 5 candidates for the software engineer role"}'
curl localhost:8000/ats/candidates
```

If `status=need_approval` (low score or no slot):
```bash
curl -X POST localhost:8000/hiring/tasks/<task_id>/approve -H 'Content-Type: application/json' -d '{"decision":"approved"}'
```

## Architecture
`planner (gpt-4o or rules) -> screener (score+ATS) -> scheduler (slots+emails) -> verifier (deterministic) -> human_gate`
Supervisor routing is pure Python. Trace per node logged to `trace.jsonl`. ATS upserts idempotent on `candidate_id`; bookings idempotent on `candidate_id+slot`.

Tools: `list_resumes`, `read_resume`, `score_resume`, `find_slots`, `send_email`, `ats_upsert`, `ats_list`.

Fault tolerance: per-tool retry, score/confidence gate, slot fallback (next free panel slot), `MAX_RETRIES` loop, verifier blocks false success (`count==N`, no double-book, ATS stage, emails sent). Gmail send failures never fail a run (mock log kept, reason in trace).

## Real Gmail invites (demo, redirect-only)
Set in local `.env` (never committed): `GMAIL_USER`, `GMAIL_APP_PASSWORD` (Google Account -> Security -> 2-Step Verification -> App passwords), `NOTIFY_EMAIL` (your inbox). Each shortlisted candidate then triggers one `[DEMO]` invite mailed to you, annotated with the intended mock recipient. Mock `@example.com` addresses are never mailed; without these vars the worker stays log-only mock.

## Design decisions
- **LangGraph** over CrewAI/AutoGen: explicit graph + HITL.
- **Split models**: planner quality (gpt-4o), scoring cost (mini).
- **Deterministic verifier**: LLM ranks, code decides done.
- **FastAPI + SQLite/JSON**: one-container deploy for 10-15h budget.

## Live demo tweaks
1. `.env SCORE_THRESHOLD=70 -> 95`: same goal now needs approval.
2. `app/agent/verifier.py`: add `no Friday 15:30+` rule.
3. Block `calendars/alice.json` with busy slots: shows re-plan to next free day.
4. Add new tool file (e.g. `background_check.py`): executor picks it up.

## Deploy
Split deploy (recommended): static frontend + container backend.
- **Backend (Render/Fly):** `render.yaml` builds the Dockerfile, health-checks `/health`,
  persists SQLite on a 1 GB disk (`ATS_DB=/app/data/ats.db`). Set `OPENAI_API_KEY`,
  Gmail vars and `CORS_ORIGINS=https://<your-frontend>` in the dashboard — never in git.
  Single uvicorn worker on purpose: SQLite needs one writer.
- **Frontend (Vercel/Netlify):** root `frontend/`, build `npm run build`, output `dist/`,
  env `VITE_API_URL=https://<your-backend>`. Local dev needs nothing (Vite proxies to :8000).
- Uploads and JD saves ride the image/disk and are ephemeral on redeploy; treat the
  deployed box as a demo, keep seeds in git.
- **Render free tier sleeps after 15 min idle.** Workarounds shipped: `.github/workflows/keep-awake.yml`
  pings `/health` every 10 min (set `RENDER_API_URL` repo variable), and the UI retries
  idempotent reads once across a cold start. Real fix: Starter plan or Fly.io.

## Limitations
- Mock resumes/calendars/emails only, no real Gmail/Outlook.
- In-memory task store; swap for Postgres/Redis later.
- Rule fallback scoring if no API key.
- Single-threaded invoke.

## Next
Real calendar OAuth, PDF resume OCR, multi-role batch, interviewer load-balancing, Langfuse traces, Celery queue.

## Models / APIs
OpenAI gpt-4o / gpt-4o-mini via langchain-openai. Other: langgraph, fastapi, uvicorn, pypdf.

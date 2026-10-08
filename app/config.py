"""Central config - live-tweak knobs."""
import os

def getenv(k: str, d: str) -> str:
    return os.getenv(k, d)

OPENAI_API_KEY = getenv("OPENAI_API_KEY", "")
PLANNER_MODEL = getenv("PLANNER_MODEL", "gpt-4o")
WORKER_MODEL = getenv("WORKER_MODEL", "gpt-4o-mini")
SCORE_THRESHOLD = float(getenv("SCORE_THRESHOLD", "70"))
TOP_N = int(getenv("TOP_N", "5"))
INTERVIEW_MINUTES = int(getenv("INTERVIEW_MINUTES", "45"))
PANEL = [p.strip() for p in getenv("PANEL", "alice,bob").split(",") if p.strip()]
ATS_DB = getenv("ATS_DB", "ats.db")
RESUME_DIR = getenv("RESUME_DIR", "seed_resumes")
CAL_DIR = getenv("CAL_DIR", "calendars")
JDS_DIR = getenv("JDS_DIR", "jds")
MAX_RETRIES = int(getenv("MAX_RETRIES", "2"))
# Real Gmail invites (redirect-only): all three set => per-candidate mail goes to NOTIFY_EMAIL.
# Mock @example.com addresses are never mailed. Absent => log-only mock (offline-safe).
GMAIL_USER = getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = getenv("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAIL = getenv("NOTIFY_EMAIL", "")

def gmail_configured() -> bool:
    return bool(GMAIL_USER and GMAIL_APP_PASSWORD and NOTIFY_EMAIL)
# Strict JD match: without an exact JD file for the role, the run stops before
# booking anything (graceful failure). Set false to allow closest-file fallback.
STRICT_JD = getenv("STRICT_JD", "true").lower() == "true"
# Role filter: screen only resumes that look like applicants for the role
# (filename/header match). Falls back to the full pool when too few match.
ROLE_FILTER = getenv("ROLE_FILTER", "true").lower() == "true"
# LLM budgets: rule-score ranks everyone; LLM refines only the head of the list.
LLM_TIMEOUT_S = float(getenv("LLM_TIMEOUT_S", "20"))
LLM_MAX_RETRIES = int(getenv("LLM_MAX_RETRIES", "1"))
LLM_RESCORE_LIMIT = int(getenv("LLM_RESCORE_LIMIT", "15"))
LLM_RESCORE_WORKERS = int(getenv("LLM_RESCORE_WORKERS", "5"))

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

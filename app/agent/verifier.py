"""Verifier: deterministic hiring checks. Extend live (e.g. no Friday PM rule)."""
from .state import HireState
from .tools_ats import ats_list
from app.config import ATS_DB

def verifier_node(state: HireState) -> dict:
    trace = list(state.get("trace", []))
    bookings = state.get("bookings", [])
    shortlist = state.get("shortlist", [])
    # 1. count matches
    if len(bookings) != len(shortlist) or not bookings:
        trace.append({"node": "verifier", "result": "FAIL", "reason": "booking count mismatch"})
        return {"status": "failed", "error": "booking count mismatch",
                "retries": int(state.get("retries", 0)) + 1, "trace": trace}
    # 2. no double-book
    slots = [b["slot"] for b in bookings]
    if len(slots) != len(set(slots)):
        trace.append({"node": "verifier", "result": "FAIL", "reason": "double-booked slot"})
        return {"status": "failed", "error": "double-booked slot",
                "retries": int(state.get("retries", 0)) + 1, "trace": trace}
    # 3. ATS stages
    rows = {c["candidate_id"]: c for c in ats_list(ATS_DB)}
    bad = [b["candidate_id"] for b in bookings if rows.get(b["candidate_id"], {}).get("stage") != "interview_scheduled"]
    if bad:
        trace.append({"node": "verifier", "result": "FAIL", "reason": f"ATS not updated: {bad}"})
        return {"status": "failed", "error": f"ATS not updated: {bad}",
                "retries": int(state.get("retries", 0)) + 1, "trace": trace}
    # 4. emails sent
    missing = [b for b in bookings if not b.get("email_id")]
    if missing:
        trace.append({"node": "verifier", "result": "FAIL", "reason": "missing emails"})
        return {"status": "failed", "error": "missing emails",
                "retries": int(state.get("retries", 0)) + 1, "trace": trace}
    trace.append({"node": "verifier", "result": "PASS", "bookings": bookings})
    return {"status": "done", "trace": trace}

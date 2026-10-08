"""Screener+Scheduler executor: score resumes, pick top-N, book conflict-free slots."""
import time
from pathlib import Path
from .state import HireState
from .tools_resumes import list_resumes, read_resume, score_resume, find_slots, send_email, load_jd
from .tools_ats import ats_upsert
from app.config import RESUME_DIR, CAL_DIR, ATS_DB, SCORE_THRESHOLD, PANEL, JDS_DIR

def _llm_score(llm, text: str, jd_text: str, fallback: dict) -> dict:
    if llm is None:
        return fallback
    try:
        r = llm.invoke([("system", 'Score resume 0-100 against the JD. JSON {"score":float,"confidence":float,"reason":str} ONLY.'),
                        ("user", f"JD:\n{jd_text[:2000]}\n\nResume:\n{text[:2500]}")])
        import json as _j
        d = _j.loads(r.content if isinstance(r.content, str) else str(r.content))
        return {"score": float(d.get("score", fallback["score"])),
                "confidence": float(d.get("confidence", 0.85)),
                "reason": d.get("reason", ""), "method": "llm"}
    except Exception as e:
        fallback["llm_error"] = str(e)
        return fallback

def screener_node(state: HireState, llm=None) -> dict:
    trace = list(state.get("trace", []))
    role = state.get("role", "software engineer")
    top_n = int(state.get("top_n", 5))
    files, scored = [], []
    for attempt in range(1, 4):
        try:
            files = list_resumes(RESUME_DIR, role)
            if files:
                trace.append({"node": "screener", "tool": "list_resumes", "attempt": attempt, "files": files})
                break
        except Exception as e:
            trace.append({"node": "screener", "attempt": attempt, "error": str(e)})
            time.sleep(0.4 * attempt)
    if not files:
        return {"status": "failed", "error": "no resumes found", "trace": trace}
    jd_text = load_jd(JDS_DIR, role)
    trace.append({"node": "screener", "jd_chars": len(jd_text)})
    for fn in files:
        info = read_resume(RESUME_DIR, fn)
        base = score_resume(info["text"], jd_text, role)
        s = _llm_score(llm, info["text"], jd_text, base)
        import re as _re
        cid = _re.sub(r"[^A-Za-z0-9_]+", "_", Path(fn).stem).strip("_")
        email = f"{cid}@example.com"
        scored.append({"candidate_id": cid, "name": info["name"], "email": email,
                       "score": s["score"], "confidence": s.get("confidence", 0.85),
                       "reason": s.get("reason", s.get("method", ""))})
        ats_upsert(ATS_DB, cid, info["name"], role, s["score"], "screened")
    scored.sort(key=lambda x: x["score"], reverse=True)
    shortlist = scored[:top_n]
    trace.append({"node": "screener", "shortlist": shortlist})
    low = [c for c in shortlist if c["score"] < SCORE_THRESHOLD or c["confidence"] < 0.7]
    if low and state.get("approval_decision") != "approved":
        return {"status": "need_approval", "shortlist": shortlist, "trace": trace,
                "error": f"Approval required: {len(low)} below threshold {SCORE_THRESHOLD}: {[c['candidate_id'] for c in low]}"}
    return {"status": "scheduling", "shortlist": shortlist, "trace": trace}

def scheduler_node(state: HireState) -> dict:
    trace = list(state.get("trace", []))
    shortlist = state.get("shortlist", [])
    slots = find_slots(CAL_DIR, PANEL)
    if len(slots) < len(shortlist):
        return {"status": "failed", "error": f"only {len(slots)} slots for {len(shortlist)} candidates", "trace": trace}
    bookings = []
    for cand, slot in zip(shortlist, slots):
        ats_upsert(ATS_DB, cand["candidate_id"], cand["name"], state.get("role", ""), cand["score"], "interview_scheduled", slot)
        mail = send_email(cand["email"], f"Interview invite: {state.get('role','')} @ {slot}",
                          f"Hi {cand['name']}, your panel interview is {slot} with " + ",".join(PANEL) + ".")
        bookings.append({"candidate_id": cand["candidate_id"], "slot": slot, "email_id": mail["id"]})
    trace.append({"node": "scheduler", "bookings": bookings})
    return {"status": "verifying", "bookings": bookings, "trace": trace}

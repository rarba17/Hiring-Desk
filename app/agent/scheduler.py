"""Screener+Scheduler executor: score resumes, pick top-N, book conflict-free slots."""
import time
from pathlib import Path
from .state import HireState
from .tools_resumes import list_resumes, read_resume, score_resume, find_slots, send_email, send_gmail_smtp, load_jd, jd_file_used, jd_is_exact, _idf_weights, _jd_keywords
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
    trace.append({"node": "screener", "jd_file": jd_file_used(JDS_DIR, role),
                  "jd_exact": jd_is_exact(JDS_DIR, role), "jd_chars": len(jd_text)})
    infos = [(fn, read_resume(RESUME_DIR, fn)) for fn in files]
    weights = _idf_weights([i["text"].lower() for _, i in infos], _jd_keywords(jd_text))
    # Rule-score everyone (free, instant), then LLM-rescore only the head of the
    # list in parallel. Bounds a 79-resume run to ~15 LLM calls instead of 79.
    from app.config import LLM_RESCORE_LIMIT, LLM_RESCORE_WORKERS
    prelim = [(fn, info, score_resume(info["text"], jd_text, role, weights)) for fn, info in infos]
    prelim.sort(key=lambda t: t[2]["score"], reverse=True)
    cands = prelim[:max(LLM_RESCORE_LIMIT, top_n)] if llm is not None else prelim
    rest = prelim[len(cands):] if llm is not None else []
    if llm is not None:
        from concurrent.futures import ThreadPoolExecutor
        def _rescore(t):
            fn, info, base = t
            return (fn, info, _llm_score(llm, info["text"], jd_text, base))
        with ThreadPoolExecutor(max_workers=LLM_RESCORE_WORKERS) as ex:
            cands = list(ex.map(_rescore, cands))
        trace.append({"node": "screener", "llm_rescored": len(cands), "rule_only": len(rest)})
    for fn, info, s in list(cands) + rest:
        import re as _re
        cid = _re.sub(r"[^A-Za-z0-9_]+", "_", Path(fn).stem).strip("_")
        email = f"{cid}@example.com"
        scored.append({"candidate_id": cid, "name": info["name"], "email": email,
                       "score": s["score"], "confidence": s.get("confidence", 0.85),
                       "reason": s.get("reason", s.get("method", ""))})
        ats_upsert(ATS_DB, cid, info["name"], role, s["score"], "screened")
    scored.sort(key=lambda x: x["score"], reverse=True)
    shortlist = scored[:top_n]
    trace.append({"node": "screener", "jd_file": jd_file_used(JDS_DIR, role),
                  "jd_exact": jd_is_exact(JDS_DIR, role), "shortlist": shortlist})
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
    from app.config import gmail_configured, NOTIFY_EMAIL
    use_gmail = gmail_configured()
    for cand, slot in zip(shortlist, slots):
        ats_upsert(ATS_DB, cand["candidate_id"], cand["name"], state.get("role", ""), cand["score"], "interview_scheduled", slot)
        subject = f"Interview invite: {state.get('role','')} @ {slot}"
        body = (f"Hi {cand['name']}, your panel interview is {slot} with " + ",".join(PANEL) + ".")
        mail = send_email(cand["email"], subject, body)
        gmail_note = "mock-log"
        if use_gmail:
            # Redirect-only: mock candidate addresses are never mailed.
            try:
                g = send_gmail_smtp(
                    NOTIFY_EMAIL, f"[DEMO] {subject}",
                    body + f"\n\n(Intended recipient: {cand['name']} <{cand['email']}> — redirected, mock address.)")
                mail = g
                gmail_note = f"gmail:{g['id']} -> {NOTIFY_EMAIL}"
            except Exception as e:
                gmail_note = f"gmail-failed({e}); kept mock log"
        bookings.append({"candidate_id": cand["candidate_id"], "slot": slot,
                         "email_id": mail["id"], "email_via": gmail_note})
    trace.append({"node": "scheduler", "bookings": bookings})
    return {"status": "verifying", "bookings": bookings, "trace": trace}

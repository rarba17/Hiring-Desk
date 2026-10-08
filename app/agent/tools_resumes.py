"""Resume + calendar + email tools (all mock files, real logic)."""
import json
import re
from pathlib import Path
from typing import List, Dict, Any

def list_resumes(resume_dir: str, role: str = "") -> List[str]:
    """Return ALL resumes. Screening ranks by JD score, so filename filtering would wrongly drop uploads."""
    p = Path(resume_dir)
    if not p.exists():
        return []
    return sorted(f.name for f in p.iterdir() if f.is_file())

def read_resume(resume_dir: str, filename: str) -> Dict[str, Any]:
    path = Path(resume_dir) / filename
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            r = PdfReader(str(path))
            text = "\n".join([(pg.extract_text() or "") for pg in r.pages])
        except Exception:
            text = ""
    else:
        text = path.read_text(errors="ignore")
    name = re.search(r"Name:\s*(.+)", text)
    if name:
        display = name.group(1).strip()
    else:
        # fallback: first non-empty line (handles real PDFs without a "Name:" label)
        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        display = first[:60] if first else filename
    skills = re.search(r"Skills:\s*(.+)", text, re.I)
    yrs = re.search(r"(\d+)\s+years?", text, re.I)
    return {"filename": filename, "text": text[:4000],
            "name": display,
            "skills": skills.group(1).strip() if skills else "",
            "years": int(yrs.group(1)) if yrs else 0}

def _jd_keywords(jd_text: str) -> List[str]:
    stop = {"and", "or", "the", "with", "for", "years", "year", "experience",
            "must", "have", "plus", "strong", "role", "skills", "requirements"}
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.]+", jd_text.lower())
    kws = [w.strip("+#.") for w in words if len(w) >= 3 and w not in stop]
    # keep order, dedupe, cap at 20
    seen, out = set(), []
    for w in kws:
        if w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) >= 20:
            break
    return out

def score_resume(text: str, jd_text: str = "", role: str = "software engineer") -> Dict[str, Any]:
    """JD-aware rule scorer. Keyword overlap with JD + years. LLM overrides when key present."""
    t = text.lower()
    kws = _jd_keywords(jd_text) if jd_text else \
        ["python", "fastapi", "react", "aws", "langchain", "llm"]
    score = 50.0
    hits = [k for k in kws if k and k in t]
    if kws:
        score += 40.0 * len(hits) / max(len(kws), 1)
    m = re.search(r"(\d+)\s+years?", t)
    if m:
        score += min(int(m.group(1)) * 2, 12)
    score = min(round(score, 1), 97.0)
    return {"score": score, "confidence": 0.85, "method": "rules-jd",
            "matched": hits[:10], "jd_keywords": kws[:10]}

def jd_key(role: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (role or "").strip().lower()).strip("_") or "default"

def jd_path(jds_dir: str, role: str) -> Path:
    return Path(jds_dir) / f"{jd_key(role)}.txt"

def read_jd_exact(jds_dir: str, role: str) -> str:
    """Exact match only (for View). The screener's load_jd keeps fallbacks."""
    p = jd_path(jds_dir, role)
    return p.read_text() if p.exists() else ""

def save_jd(jds_dir: str, role: str, text: str) -> str:
    p = Path(jds_dir)
    p.mkdir(parents=True, exist_ok=True)
    key = jd_key(role)
    (p / f"{key}.txt").write_text(text)
    return key

def delete_jd(jds_dir: str, role: str) -> bool:
    p = jd_path(jds_dir, role)
    if p.exists():
        p.unlink()
        return True
    return False

def load_jd(jds_dir: str, role: str) -> str:
    p = jd_path(jds_dir, role)
    if p.exists():
        return p.read_text()
    # fallback: any JD containing role token, else first JD, else ""
    if Path(jds_dir).exists():
        token = role.strip().split()[0].lower() if role.strip() else ""
        for f in sorted(Path(jds_dir).iterdir()):
            if f.is_file() and (token in f.name.lower() or token in f.read_text(errors="ignore").lower()):
                return f.read_text()
        files = sorted(f for f in Path(jds_dir).iterdir() if f.is_file())
        if files:
            return files[0].read_text()
    return ""

def list_jds(jds_dir: str) -> List[str]:
    p = Path(jds_dir)
    if not p.exists():
        return []
    return sorted(f.name for f in p.iterdir() if f.is_file())

def load_calendar(cal_dir: str, person: str) -> Dict[str, Any]:
    p = Path(cal_dir) / f"{person}.json"
    if not p.exists():
        return {"busy": []}
    return json.loads(p.read_text())

def find_slots(cal_dir: str, panel: List[str], duration_min: int = 45) -> List[str]:
    """Deterministic slot finder over mock week. Returns conflict-free slots."""
    days = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
    hours = ["10:00", "11:30", "14:00", "15:30"]
    busy = {}
    for person in panel:
        busy[person] = set(load_calendar(cal_dir, person).get("busy", []))
    free = []
    for d in days:
        for h in hours:
            slot = f"{d}T{h}"
            if all(slot not in busy.get(p, set()) for p in panel):
                free.append(slot)
    return free

def send_email(to: str, subject: str, body: str, log_path: str = "emails_sent.jsonl") -> Dict[str, Any]:
    import json as _j
    eid = f"mail_{abs(hash(to+subject)) % 10**6}"
    rec = {"id": eid, "to": to, "subject": subject, "body": body[:500]}
    with open(log_path, "a") as f:
        f.write(_j.dumps(rec) + "\n")
    return {"ok": True, "id": eid}

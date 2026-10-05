"""Resume + calendar + email tools (all mock files, real logic)."""
import json
import re
from pathlib import Path
from typing import List, Dict, Any

def list_resumes(resume_dir: str, role: str = "") -> List[str]:
    p = Path(resume_dir)
    if not p.exists():
        return []
    files = sorted(f.name for f in p.iterdir() if f.is_file())
    if role:
        token = re.split(r"[^A-Za-z0-9]+", role.strip())[0].lower()
        matched = [f for f in files if token in f.lower() or "swe" in f.lower() or "software" in f.lower()]
        return matched or files
    return files

def read_resume(resume_dir: str, filename: str) -> Dict[str, Any]:
    text = (Path(resume_dir) / filename).read_text(errors="ignore")
    name = re.search(r"Name:\s*(.+)", text)
    skills = re.search(r"Skills:\s*(.+)", text, re.I)
    yrs = re.search(r"(\d+)\s+years?", text, re.I)
    return {"filename": filename, "text": text[:4000],
            "name": name.group(1).strip() if name else filename,
            "skills": skills.group(1).strip() if skills else "",
            "years": int(yrs.group(1)) if yrs else 0}

def score_resume(text: str, role: str = "software engineer") -> Dict[str, Any]:
    """Rule-based fallback scorer. LLM overrides when key present."""
    t = text.lower()
    score = 50.0
    for kw, pts in [("python", 10), ("fastapi", 8), ("react", 5), ("aws", 5), ("langchain", 7), ("llm", 7)]:
        if kw in t:
            score += pts
    m = re.search(r"(\d+)\s+years?", t)
    if m:
        score += min(int(m.group(1)) * 2, 12)
    score = min(score, 97.0)
    return {"score": round(score, 1), "confidence": 0.85, "method": "rules"}

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

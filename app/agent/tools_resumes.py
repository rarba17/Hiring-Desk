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
    m = re.search(r"\*\*Name:\*\*\s*(.+)", text) or re.search(r"Name:\s*(.+)", text)
    if m:
        display = re.sub(r"\*", "", m.group(1)).strip()
    else:
        # fallback: first content line that is not a separator (===, ---) or label
        display = filename
        for ln in text.splitlines():
            s = re.sub(r"\*", "", ln).strip()
            if not s or len(re.sub(r"[^A-Za-z]", "", s)) < 3:
                continue
            if re.fullmatch(r"[^A-Za-z0-9 ]+", s):
                continue
            display = s[:60]
            break
    skills = re.search(r"Skills:\s*(.+)", text, re.I)
    ym = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+years?", text, re.I)
    wordnum = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
               "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
    yrs = 0
    if ym:
        yrs = min(int(ym.group(1)) if ym.group(1).isdigit() else wordnum.get(ym.group(1).lower(), 0), 30)
    return {"filename": filename, "text": text[:4000],
            "name": display,
            "skills": skills.group(1).strip() if skills else "",
            "years": yrs}

def _jd_keywords(jd_text: str) -> List[str]:
    """Skill-first extraction: comma-separated Skills/Requirements lines win.
    Falls back to distinctive words (generic filler excluded)."""
    stop = {"and", "or", "the", "with", "for", "years", "year", "experience",
            "must", "have", "plus", "strong", "role", "skills", "requirements",
            "summary", "design", "implement", "monitor", "robust", "core",
            "build", "real", "time", "work", "team", "ability", "including",
            "using", "used", "within", "across", "such", "will", "our"}
    skills: List[str] = []
    for ln in jd_text.splitlines():
        if re.match(r"\s*(skills|requirements|must have|tech stack|core expertise)\b", ln, re.I):
            chunk = re.split(r":", ln, maxsplit=1)[-1]
            for part in re.split(r"[,|/]", chunk):
                w = part.strip().lower()
                w = re.sub(r"\(.*?\)", "", w).strip()
                if 2 <= len(w) <= 30 and w not in stop:
                    skills.append(w)
    if skills:
        seen, out = set(), []
        for w in skills:
            if w not in seen:
                seen.add(w)
                out.append(w)
            if len(out) >= 15:
                break
        return out
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.]+", jd_text.lower())
    kws = [w.strip("+#.") for w in words if len(w) >= 4 and w not in stop]
    seen, out = set(), []
    for w in kws:
        if w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) >= 15:
            break
    return out

def _idf_weights(texts: List[str], keywords: List[str]) -> Dict[str, float]:
    """Rare-across-the-pool keywords count more than ubiquitous ones."""
    import math
    n = max(len(texts), 1)
    w = {}
    for k in keywords:
        df = sum(1 for t in texts if k and k in t) or 1
        w[k] = round(1.0 + math.log(n / df), 2)
    return w

def score_resume(text: str, jd_text: str = "", role: str = "software engineer",
                 weights: Dict[str, float] = None) -> Dict[str, Any]:
    """JD-aware rule scorer: IDF-weighted skill overlap + experience. LLM overrides when key present."""
    t = text.lower()
    kws = _jd_keywords(jd_text) if jd_text else \
        ["python", "fastapi", "react", "aws", "langchain", "llm"]
    w = weights or {}
    total = sum(w.get(k, 1.0) for k in kws) or 1.0
    skill_line = " ".join(ln for ln in t.splitlines() if "skill" in ln or "expertise" in ln)
    hits, got = [], 0.0
    for k in kws:
        if not k or k not in t:
            continue
        hits.append(k)
        wk = w.get(k, 1.0)
        freq = min(t.count(k), 3) / 3.0          # repeated, deliberate use counts more
        claimed = 1.0 if k in skill_line else 0.0  # listed under Skills counts more
        got += wk * (1.0 + 0.5 * freq + 0.5 * claimed)
    score = 35.0 + 50.0 * got / (2.0 * total)
    wordnum = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
               "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
    m = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+years?", t)
    yrs = 0
    if m:
        tok = m.group(1)
        yrs = min(int(tok) if tok.isdigit() else wordnum.get(tok, 0), 10)
    score += yrs  # 0-10 pts: experience separates otherwise tied resumes
    score = min(round(score, 1), 97.0)
    reason = f"matched {', '.join(hits[:6])} (+{yrs}y)" if hits else "no skill overlap"
    return {"score": score, "confidence": 0.85, "method": "rules-jd",
            "matched": hits[:10], "jd_keywords": kws[:10], "reason": reason}

def jd_key(role: str) -> str:
    # engineer ~ developer: "Python Backend Engineer" and "Python Backend
    # Developer" are the same role and must resolve to one file.
    norm = (role or "").strip().lower()
    norm = re.sub(r"\bengineers?\b", "developer", norm)
    return re.sub(r"[^a-z0-9]+", "_", norm).strip("_") or "default"

def _jd_literal_key(role: str) -> str:
    """Pre-synonym spelling, so files saved as *-engineer.txt keep resolving."""
    return re.sub(r"[^a-z0-9]+", "_", (role or "").strip().lower()).strip("_") or "default"

def jd_path(jds_dir: str, role: str) -> Path:
    return Path(jds_dir) / f"{jd_key(role)}.txt"

def _jd_existing(jds_dir: str, role: str) -> Path | None:
    """Canonical file, literal-spelling file, or a file whose name covers all
    role tokens ("Golang Engineer" -> go_golang_engineer.txt). Else None."""
    for key in (jd_key(role), _jd_literal_key(role)):
        p = Path(jds_dir) / f"{key}.txt"
        if p.exists():
            return p
    rtoks = set(re.findall(r"[a-z0-9]+", jd_key(role).replace("_", " ")))
    rtoks.discard("developer")  # engineer/developer already canonicalized
    if rtoks and Path(jds_dir).exists():
        for f in sorted(Path(jds_dir).iterdir()):
            if f.is_file() and rtoks <= set(re.findall(r"[a-z0-9]+", f.stem.lower())):
                return f
    return None

def read_jd_exact(jds_dir: str, role: str) -> str:
    """Exact match only (for View). The screener's load_jd keeps fallbacks."""
    p = _jd_existing(jds_dir, role)
    return p.read_text() if p else ""

def save_jd(jds_dir: str, role: str, text: str) -> str:
    p = Path(jds_dir)
    p.mkdir(parents=True, exist_ok=True)
    key = jd_key(role)
    (p / f"{key}.txt").write_text(text)
    return key

def delete_jd(jds_dir: str, role: str) -> bool:
    p = _jd_existing(jds_dir, role)
    if p:
        p.unlink()
        return True
    return False

def load_jd(jds_dir: str, role: str) -> str:
    p = _jd_existing(jds_dir, role)
    if p:
        return p.read_text()
    # best match: JD file sharing the most tokens with the role (deterministic)
    if Path(jds_dir).exists():
        rtoks = set(re.findall(r"[a-z0-9]+", role.lower()))
        best, best_hit = None, 0
        for f in sorted(Path(jds_dir).iterdir()):
            if not f.is_file():
                continue
            ftoks = set(re.findall(r"[a-z0-9]+", f.stem.lower()))
            hit = len(rtoks & ftoks)
            if hit > best_hit:
                best, best_hit = f, hit
        if best:
            return best.read_text()
        files = sorted(f for f in Path(jds_dir).iterdir() if f.is_file())
        if files:
            return files[0].read_text()
    return ""

def jd_file_used(jds_dir: str, role: str) -> str:
    """Which JD file load_jd resolves to (for trace transparency)."""
    p = _jd_existing(jds_dir, role)
    if p:
        return p.name
    if Path(jds_dir).exists():
        rtoks = set(re.findall(r"[a-z0-9]+", role.lower()))
        best, best_hit = None, 0
        for f in sorted(Path(jds_dir).iterdir()):
            if not f.is_file():
                continue
            hit = len(rtoks & set(re.findall(r"[a-z0-9]+", f.stem.lower())))
            if hit > best_hit:
                best, best_hit = f, hit
        if best:
            return best.name
    return ""

def jd_is_exact(jds_dir: str, role: str) -> bool:
    """True when a JD file exists for this exact role (no fallback guessing)."""
    return _jd_existing(jds_dir, role) is not None

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

def send_gmail_smtp(to: str, subject: str, body: str, timeout: int = 15) -> Dict[str, Any]:
    """Real send via Gmail SMTP (app password). Raises on failure; caller decides fallback."""
    import smtplib
    from email.message import EmailMessage
    from app.config import GMAIL_USER, GMAIL_APP_PASSWORD
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=timeout) as s:
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.send_message(msg)
    return {"ok": True, "id": f"gmail_{abs(hash(to+subject)) % 10**6}"}

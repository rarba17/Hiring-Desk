"""ATS mock - applicant tracking system. Idempotent on candidate_id."""
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
  candidate_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  score REAL DEFAULT 0,
  stage TEXT DEFAULT 'applied',
  slot TEXT DEFAULT '',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def _conn(db: str):
    p = Path(db)
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(p))
    c.execute(SCHEMA)
    c.commit()
    return c

def ats_upsert(db: str, candidate_id: str, name: str, role: str, score: float = 0, stage: str = "applied", slot: str = "") -> dict:
    c = _conn(db)
    cur = c.cursor()
    cur.execute("SELECT candidate_id FROM candidates WHERE candidate_id=?", (candidate_id,))
    exists = cur.fetchone()
    if exists:
        cur.execute("UPDATE candidates SET name=?, role=?, score=?, stage=?, slot=? WHERE candidate_id=?",
                    (name, role, score, stage, slot, candidate_id))
    else:
        cur.execute("INSERT INTO candidates (candidate_id,name,role,score,stage,slot) VALUES (?,?,?,?,?,?)",
                    (candidate_id, name, role, score, stage, slot))
    c.commit()
    c.close()
    return {"ok": True, "candidate_id": candidate_id, "stage": stage, "duplicate": bool(exists)}

def ats_get(db: str, candidate_id: str) -> Optional[dict]:
    c = _conn(db)
    cur = c.cursor()
    cur.execute("SELECT candidate_id,name,role,score,stage,slot FROM candidates WHERE candidate_id=?", (candidate_id,))
    r = cur.fetchone()
    c.close()
    if not r:
        return None
    return {"candidate_id": r[0], "name": r[1], "role": r[2], "score": r[3], "stage": r[4], "slot": r[5]}

def ats_list(db: str, role: str = "") -> List[dict]:
    c = _conn(db)
    cur = c.cursor()
    if role:
        # fuzzy match: old runs may store longer role strings ("all candidates for the X")
        cur.execute("SELECT candidate_id,name,role,score,stage,slot FROM candidates WHERE LOWER(role) LIKE ? ORDER BY score DESC",
                    (f"%{role.strip().lower()}%",))
    else:
        cur.execute("SELECT candidate_id,name,role,score,stage,slot FROM candidates ORDER BY score DESC")
    rows = cur.fetchall()
    c.close()
    return [{"candidate_id": r[0], "name": r[1], "role": r[2], "score": r[3], "stage": r[4], "slot": r[5]} for r in rows]

"""FastAPI hiring worker API."""
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from app.agent.graph import build_graph
from app.agent.tools_ats import ats_list
from app.agent.tools_resumes import save_jd, load_jd, list_jds, list_resumes, delete_jd, read_jd_exact
from app.api.store import new_task_id, save_task, get_task, log_trace
from app.config import ATS_DB, JDS_DIR, RESUME_DIR

app = FastAPI(title="Hiring Worker", version="0.1.0")
try:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
except Exception:
    pass
graph = build_graph()

class GoalRequest(BaseModel):
    goal: str

class ApproveRequest(BaseModel):
    decision: str = "approved"

class JDRequest(BaseModel):
    role: str
    text: str

def _run(goal: str, approval: str = "") -> dict:
    out = graph.invoke({"goal": goal, "retries": 0, "trace": [], "approval_decision": approval})
    log_trace(goal, out)
    return out

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/hiring/tasks")
def create_task(req: GoalRequest):
    tid = new_task_id()
    res = _run(req.goal)
    save_task(tid, {"goal": req.goal, "result": res})
    return {"task_id": tid, "status": res.get("status"), "result": res}

@app.get("/hiring/tasks/{tid}")
def read_task(tid: str):
    d = get_task(tid)
    if not d:
        raise HTTPException(404, "unknown task_id")
    return {"task_id": tid, **d}

@app.post("/hiring/tasks/{tid}/approve")
def approve(tid: str, req: ApproveRequest):
    d = get_task(tid)
    if not d:
        raise HTTPException(404, "unknown task_id")
    if req.decision not in ("approved", "rejected"):
        raise HTTPException(400, "decision must be approved|rejected")
    if req.decision == "rejected":
        d["result"]["status"] = "failed"
        d["result"]["error"] = "rejected by user"
        save_task(tid, d)
        return {"task_id": tid, **d}
    res = _run(d["goal"], approval="approved")
    save_task(tid, {"goal": d["goal"], "result": res})
    return {"task_id": tid, "status": res.get("status"), "result": res}

@app.get("/ats/candidates")
def candidates(role: str = ""):
    return {"candidates": ats_list(ATS_DB, role)}

@app.post("/jds")
def upsert_jd(req: JDRequest):
    key = save_jd(JDS_DIR, req.role, req.text)
    return {"ok": True, "role": req.role, "key": key, "chars": len(req.text)}

@app.get("/jds")
def jd_list():
    return {"jds": list_jds(JDS_DIR)}

@app.get("/jds/{role}")
def jd_get(role: str):
    text = read_jd_exact(JDS_DIR, role)
    if not text:
        raise HTTPException(404, "no JD for role")
    return {"role": role, "text": text}

@app.delete("/jds/{role}")
def jd_delete(role: str):
    if not delete_jd(JDS_DIR, role):
        raise HTTPException(404, "no JD for role")
    return {"ok": True, "role": role}

@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    from pathlib import Path
    dest_dir = Path(RESUME_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    name = Path(file.filename or "resume.txt").name
    # allow txt/md/pdf only
    if Path(name).suffix.lower() not in (".txt", ".md", ".pdf"):
        raise HTTPException(400, "use .txt, .md or .pdf")
    (dest_dir / name).write_bytes(data)
    return {"ok": True, "filename": name, "bytes": len(data),
            "resumes": list_resumes(str(dest_dir))}

@app.get("/")
def root():
    return {"service": "hiring-worker", "docs": "/docs", "ui": "/ui"}

@app.get("/ui")
def ui():
    from fastapi.responses import HTMLResponse
    from pathlib import Path
    return HTMLResponse(Path(__file__).with_name("ui.html").read_text())

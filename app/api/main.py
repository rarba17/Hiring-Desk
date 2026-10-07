"""FastAPI hiring worker API."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from app.agent.graph import build_graph
from app.agent.tools_ats import ats_list
from app.api.store import new_task_id, save_task, get_task, log_trace
from app.config import ATS_DB

app = FastAPI(title="Hiring Worker", version="0.1.0")
graph = build_graph()

class GoalRequest(BaseModel):
    goal: str

class ApproveRequest(BaseModel):
    decision: str = "approved"

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

@app.get("/")
def root():
    return {"service": "hiring-worker", "docs": "/docs"}

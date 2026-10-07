"""In-memory hiring task store + trace log."""
import json
import uuid
from typing import Dict, Any

TASKS: Dict[str, Dict[str, Any]] = {}

def new_task_id() -> str:
    return uuid.uuid4().hex[:8]

def save_task(tid: str, data: Dict[str, Any]) -> None:
    TASKS[tid] = data

def get_task(tid: str) -> Dict[str, Any]:
    return TASKS.get(tid, {})

def log_trace(goal: str, result: Dict[str, Any]) -> None:
    try:
        with open("trace.jsonl", "a") as f:
            f.write(json.dumps({"goal": goal, "status": result.get("status"),
                                "bookings": result.get("bookings", []),
                                "trace": result.get("trace", [])}) + "\n")
    except Exception:
        pass

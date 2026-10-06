"""Planner: NL goal -> hiring plan JSON. OpenAI if key, else rules."""
import json
import re
from .state import HireState

SYSTEM = """You are a hiring planner. Return ONLY JSON:
{"role": str, "top_n": int, "panel": [str], "duration_min": int, "success_criteria": str}"""

def _rule(goal: str, top_n: int, panel: list) -> dict:
    m = re.search(r"top\s+(\d+)", goal, re.I)
    n = int(m.group(1)) if m else top_n
    r = re.search(r"for (?:the )?([A-Za-z ]+?) role", goal, re.I)
    role = r.group(1).strip() if r else "software engineer"
    return {"role": role, "top_n": n, "panel": panel, "duration_min": 45,
            "success_criteria": f"{n} bookings, no double-book, ATS=interview_scheduled, emails sent"}

def planner_node(state: HireState, llm=None, top_n: int = 5, panel: list = None) -> dict:
    from app.config import TOP_N, PANEL
    panel = panel if panel is not None else PANEL
    plan = _rule(state.get("goal", ""), TOP_N if top_n == 5 else top_n, panel)
    if llm is not None:
        try:
            resp = llm.invoke([("system", SYSTEM), ("user", state.get("goal", ""))])
            d = json.loads(resp.content if isinstance(resp.content, str) else str(resp.content))
            plan.update({k: d[k] for k in ("role", "top_n", "panel", "duration_min") if k in d})
        except Exception as e:
            plan["_llm_error"] = str(e)
    trace = list(state.get("trace", [])) + [{"node": "planner", "plan": plan}]
    return {"role": plan["role"], "top_n": plan["top_n"], "status": "planned",
            "retries": state.get("retries", 0), "trace": trace}

"""LangGraph supervisor: planner -> screener -> scheduler -> verifier + human gate."""
from langgraph.graph import StateGraph, START, END


from .state import HireState
from .planner import planner_node
from .scheduler import screener_node, scheduler_node
from .verifier import verifier_node
from app.config import MAX_RETRIES, OPENAI_API_KEY, TOP_N, PANEL

def _llm(model: str):
    if not OPENAI_API_KEY:
        return None
    try:
        from langchain_openai import ChatOpenAI
        from app.config import LLM_TIMEOUT_S, LLM_MAX_RETRIES
        return ChatOpenAI(model=model, temperature=0,
                          timeout=LLM_TIMEOUT_S, max_retries=LLM_MAX_RETRIES)
    except Exception:
        return None

def human_gate_node(state: HireState) -> dict:
    trace = list(state.get("trace", [])) + [{"node": "human_gate", "waiting": True}]
    return {"status": "need_approval", "trace": trace}

def route(state: HireState) -> str:
    s = state.get("status", "")
    if s == "planned":
        return "screener"
    if s == "scheduling":
        return "scheduler"
    if s == "verifying":
        return "verifier"
    if s == "need_approval":
        return "human_gate"
    if s == "done":
        return END
    if s == "failed":
        if int(state.get("retries", 0)) < MAX_RETRIES and state.get("approval_decision") != "rejected":
            return "screener"
        return END
    return END

def build_graph():
    from app.config import PLANNER_MODEL, WORKER_MODEL
    pl, wk = _llm(PLANNER_MODEL), _llm(WORKER_MODEL)
    g = StateGraph(HireState)
    g.add_node("planner", lambda s: planner_node(s, llm=pl))
    g.add_node("screener", lambda s: screener_node(s, llm=wk))
    g.add_node("scheduler", scheduler_node)
    g.add_node("verifier", verifier_node)
    g.add_node("human_gate", human_gate_node)
    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", route, {"screener": "screener", "scheduler": "scheduler", "verifier": "verifier", "human_gate": "human_gate", END: END})
    g.add_conditional_edges("screener", route, {"scheduler": "scheduler", "human_gate": "human_gate", "screener": "screener", END: END})
    g.add_conditional_edges("scheduler", route, {"verifier": "verifier", END: END})
    g.add_conditional_edges("verifier", route, {"screener": "screener", END: END})
    g.add_edge("human_gate", END)
    return g.compile()

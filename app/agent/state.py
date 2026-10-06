"""Shared LangGraph state for hiring worker."""
from typing import TypedDict, List, Dict, Any

class HireState(TypedDict, total=False):
    goal: str
    role: str
    top_n: int
    shortlist: List[Dict[str, Any]]
    bookings: List[Dict[str, Any]]
    retries: int
    status: str
    trace: List[Dict[str, Any]]
    error: str
    approval_decision: str

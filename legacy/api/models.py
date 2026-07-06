"""API Models."""

from pydantic import BaseModel
from typing import Dict, Any, List

class PlanRequest(BaseModel):
    """Request to the planner."""
    user_request: str

class ExecuteRequest(BaseModel):
    """Request to execute an instruction."""
    agent_name: str
    instruction: Dict[str, Any]

"""Session and Execution Models."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

class ToolExecutionRecord(BaseModel):
    """Structured record of a single tool execution."""
    tool_name: str
    intent: str
    parameters: Dict[str, Any]
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    safety_tier: str = "READ_ONLY"
    approved: bool = True
    rolled_back: bool = False

class TransactionRecord(BaseModel):
    """Record of an entire execution plan (transaction)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    goal: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_executions: List[ToolExecutionRecord] = Field(default_factory=list)
    success: bool = False
    
class Interaction(BaseModel):
    """A single user interaction loop (Request -> Plan -> Transaction)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_request: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transaction_id: Optional[str] = None

class Session(BaseModel):
    """Stateful tracking of a conversation/execution session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.utcnow)



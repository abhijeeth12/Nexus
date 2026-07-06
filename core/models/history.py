"""Execution History representing the permanent audit trail."""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

class CapabilityExecution(BaseModel):
    """Immutable record of a capability invocation."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capability_name: str
    capability_version: str
    status: str = "CREATED"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: List[str] = Field(default_factory=list) # List of generated WorkflowObject IDs
    
    logs: List[str] = Field(default_factory=list)
    exception: Optional[str] = None
    retry_count: int = 0
    
    execution_cost: float = 0.0
    token_usage: Dict[str, int] = Field(default_factory=dict)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    worker_id: Optional[str] = None

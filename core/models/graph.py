"""Execution Graph and Task State Machine."""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timezone

class TaskState(str, Enum):
    """Rigorous state machine for Task Lifecycle."""
    CREATED = "CREATED"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CACHED = "CACHED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    ROLLED_BACK = "ROLLED_BACK"

class TaskNode(BaseModel):
    """A node in the executable TaskGraph."""
    task_id: str
    capability_name: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outputs: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    
    state: TaskState = TaskState.CREATED
    priority: int = 1
    
    # Execution Policies
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = 60000
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # State tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_id: Optional[str] = None
    
    def transition(self, new_state: TaskState) -> None:
        self.state = new_state
        self.updated_at = datetime.now(timezone.utc)

class TaskGraph(BaseModel):
    """The executable task DAG managed by the Scheduler."""
    workflow_id: str
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)

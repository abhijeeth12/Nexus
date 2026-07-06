"""Models for tool execution context and results."""

from typing import Any, Dict, Optional
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

class SafetyTier(str, Enum):
    """Semantic safety classification for tools."""
    READ_ONLY = "READ_ONLY"
    RESOURCE_INTENSIVE = "RESOURCE_INTENSIVE"
    REVERSIBLE_CHANGE = "REVERSIBLE_CHANGE"
    IRREVERSIBLE_CHANGE = "IRREVERSIBLE_CHANGE"
    SYSTEM_CHANGE = "SYSTEM_CHANGE"

class ExecutionResult(BaseModel):
    """The result of executing a tool."""
    success: bool = Field(..., description="Whether the tool execution was successful.")
    output: Optional[Any] = Field(default=None, description="The primary output of the tool.")
    error: Optional[str] = Field(default=None, description="Error message if the execution failed.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or metadata.")

class ToolContext(BaseModel):
    """Context provided to a tool during execution."""
    transaction_id: str = Field(..., description="Unique ID for the current execution transaction.")
    working_directory: str = Field(..., description="The current working directory.")
    session_id: Optional[str] = Field(default=None, description="The current conversational session ID.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters passed during execution.")
    state: Dict[str, Any] = Field(default_factory=dict, description="Internal state for rollback logic.")
    workflow_state: Optional[Any] = Field(default=None, exclude=True, description="Reference to the shared WorkflowState for dataset operations.")

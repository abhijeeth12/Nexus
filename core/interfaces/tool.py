"""Tool interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from typing import Any, Dict

from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class ITool(ABC):
    """Abstract interface for an executable tool."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass
        
    @property
    @abstractmethod
    def safety_tier(self) -> SafetyTier:
        """Semantic safety classification of this tool."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Any:
        """Pydantic model representing the input schema for this tool."""
        pass

    @abstractmethod
    def validate(self, **kwargs: Any) -> bool:
        """Validate the inputs before execution."""
        pass

    @abstractmethod
    def execute(self, context: ToolContext, **kwargs: Any) -> ExecutionResult:
        """Execute the tool's core logic."""
        pass

    @abstractmethod
    def rollback(self, context: ToolContext) -> ExecutionResult:
        """Revert the tool's effects (if destructive)."""
        pass

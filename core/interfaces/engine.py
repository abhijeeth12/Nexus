"""Execution engine interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from core.interfaces.tool import ITool
from core.models.tool_context import ExecutionResult

class IExecutionEngine(ABC):
    """Abstract interface for the Execution Engine."""
    
    @abstractmethod
    def submit(self, tool: ITool, **kwargs: Any) -> ExecutionResult:
        """Submit a tool for execution."""
        pass

    @abstractmethod
    def abort(self, transaction_id: str) -> bool:
        """Abort a transaction and rollback any executed destructive tools."""
        pass

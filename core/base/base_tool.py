"""Base tool implementation."""

from abc import abstractmethod
from typing import Any, Type
from pydantic import BaseModel, ValidationError

from core.interfaces.tool import ITool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class BaseTool(ITool):
    """
    Base class for tools enforcing the Command Pattern.
    Subclasses must implement:
    - name, description, safety_tier properties
    - input_schema property (Pydantic model)
    - _execute_impl
    - _rollback_impl (if safety_tier indicates reversible/destructive)
    """

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        """Pydantic model representing the input schema for this tool."""
        pass

    def validate(self, **kwargs: Any) -> bool:
        """Validate the inputs before execution using the input_schema."""
        try:
            self.input_schema(**kwargs)
            return True
        except ValidationError:
            return False

    def execute(self, context: ToolContext, **kwargs: Any) -> ExecutionResult:
        """
        Execute the tool's core logic with validation and error handling.
        """
        try:
            parsed_kwargs = self.input_schema(**kwargs)
            return self._execute_impl(context, parsed_kwargs)
        except ValidationError as e:
            return ExecutionResult(success=False, error=f"Validation error: {e}")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Execution error: {e}")

    def rollback(self, context: ToolContext) -> ExecutionResult:
        """
        Revert the tool's effects safely.
        """
        if self.safety_tier in (SafetyTier.READ_ONLY, SafetyTier.RESOURCE_INTENSIVE):
            return ExecutionResult(
                success=True, 
                output="Tool is not state-changing, rollback skipped."
            )
        try:
            return self._rollback_impl(context)
        except Exception as e:
            return ExecutionResult(success=False, error=f"Rollback error: {e}")

    @abstractmethod
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        """Internal execution implementation to be overridden by subclasses."""
        pass

    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        """Internal rollback implementation. Should be overridden if tool changes state."""
        return ExecutionResult(success=False, error="Rollback not implemented.")

"""Base tool tests."""

import pytest
from pydantic import BaseModel, Field
from typing import Any

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class DummyInput(BaseModel):
    message: str = Field(..., description="Message to echo")
    count: int = Field(1, description="Number of times to echo")

class DummyTool(BaseTool):
    @property
    def name(self) -> str: return "dummy_echo"
    
    @property
    def description(self) -> str: return "Echos a message"
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    @property
    def input_schema(self) -> Any: return DummyInput

    def _execute_impl(self, context: ToolContext, parsed_kwargs: DummyInput) -> ExecutionResult:
        if parsed_kwargs.message == "fail":
            raise ValueError("Intentional failure")
        return ExecutionResult(
            success=True, 
            output=parsed_kwargs.message * parsed_kwargs.count
        )

class DestructiveDummyTool(DummyTool):
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.IRREVERSIBLE_CHANGE

    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Rollback successful")

def test_base_tool_validation() -> None:
    tool = DummyTool()
    assert tool.validate(message="hello") is True
    assert tool.validate(message="hello", count=2) is True
    assert tool.validate(count=2) is False  # missing required 'message'

def test_base_tool_execution_success() -> None:
    tool = DummyTool()
    ctx = ToolContext(transaction_id="tx_123", working_directory="/tmp")
    result = tool.execute(ctx, message="hi", count=2)
    assert result.success is True
    assert result.output == "hihi"
    assert result.error is None

def test_base_tool_execution_validation_error() -> None:
    tool = DummyTool()
    ctx = ToolContext(transaction_id="tx_123", working_directory="/tmp")
    result = tool.execute(ctx, count=2)  # missing 'message'
    assert result.success is False
    assert result.error is not None
    assert "Validation error" in result.error

def test_base_tool_execution_internal_error() -> None:
    tool = DummyTool()
    ctx = ToolContext(transaction_id="tx_123", working_directory="/tmp")
    result = tool.execute(ctx, message="fail")
    assert result.success is False
    assert result.error is not None
    assert "Execution error" in result.error

def test_base_tool_rollback_skipped() -> None:
    tool = DummyTool()
    ctx = ToolContext(transaction_id="tx_123", working_directory="/tmp")
    result = tool.rollback(ctx)
    assert result.success is True
    assert "rollback skipped" in str(result.output)

def test_base_tool_rollback_executed() -> None:
    tool = DestructiveDummyTool()
    ctx = ToolContext(transaction_id="tx_123", working_directory="/tmp")
    result = tool.rollback(ctx)
    assert result.success is True
    assert result.output == "Rollback successful"

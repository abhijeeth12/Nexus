"""Tests for Execution Engine."""

import pytest
from typing import Any

from engine.execution_engine import ExecutionEngine
from engine.transaction import TransactionManager
from engine.approval import MockApprovalProvider
from core.models.tool_context import ToolContext, ExecutionResult, SafetyTier
from core.interfaces.tool import ITool

class MockTool(ITool):
    def __init__(self, safety_tier: SafetyTier = SafetyTier.READ_ONLY, execute_success: bool = True):
        self._safety_tier = safety_tier
        self.execute_success = execute_success
        self.rollback_called = False
        
    @property
    def name(self) -> str: return "mock"
    @property
    def description(self) -> str: return ""
    @property
    def safety_tier(self) -> SafetyTier: return self._safety_tier
    @property
    def input_schema(self) -> Any: return None
    
    def validate(self, **kwargs: Any) -> bool: return True
    
    def execute(self, context: Any, **kwargs: Any) -> ExecutionResult:
        if self.execute_success:
            return ExecutionResult(success=True)
        return ExecutionResult(success=False, error="Failed")
        
    def rollback(self, context: Any) -> ExecutionResult:
        self.rollback_called = True
        return ExecutionResult(success=True)

def test_execution_engine_success() -> None:
    tm = TransactionManager()
    engine = ExecutionEngine(tm)
    ctx = ToolContext(transaction_id="tx_1", working_directory=".")
    tool = MockTool()
    
    res = engine.submit(tool, context=ctx)
    assert res.success is True
    
    history = tm.get_transaction_history("tx_1")
    assert len(history) == 1

def test_execution_engine_approval_rejected() -> None:
    tm = TransactionManager()
    approval = MockApprovalProvider(approve=False)
    engine = ExecutionEngine(tm, approval)
    ctx = ToolContext(transaction_id="tx_1", working_directory=".")
    
    # Destructive tool
    tool = MockTool(safety_tier=SafetyTier.IRREVERSIBLE_CHANGE)
    res = engine.submit(tool, context=ctx)
    
    assert res.success is False
    assert "rejected" in str(res.error)

def test_execution_engine_abort() -> None:
    tm = TransactionManager()
    engine = ExecutionEngine(tm)
    ctx = ToolContext(transaction_id="tx_1", working_directory=".")
    
    tool1 = MockTool()
    tool2 = MockTool()
    
    engine.submit(tool1, context=ctx)
    engine.submit(tool2, context=ctx)
    
    success = engine.abort("tx_1")
    assert success is True
    assert tool1.rollback_called is True
    assert tool2.rollback_called is True

"""Tests for Transaction Manager."""

import pytest

from engine.transaction import TransactionManager
from core.models.tool_context import ToolContext, SafetyTier
from core.interfaces.tool import ITool
from typing import Any

class DummyTool(ITool):
    def __init__(self, name: str):
        self._name = name
    @property
    def name(self) -> str: return self._name
    @property
    def description(self) -> str: return ""
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    @property
    def input_schema(self) -> Any: return None
    def validate(self, **kwargs: Any) -> bool: return True
    def execute(self, context: Any, **kwargs: Any) -> Any: pass
    def rollback(self, context: Any) -> Any: pass

def test_transaction_manager_lifo() -> None:
    tm = TransactionManager()
    tx = "tx_1"
    ctx = ToolContext(transaction_id=tx, working_directory=".")
    
    tool1 = DummyTool("t1")
    tool2 = DummyTool("t2")
    
    tm.create_transaction(tx)
    tm.add_executed_tool(tx, tool1, ctx)
    tm.add_executed_tool(tx, tool2, ctx)
    
    history = tm.get_transaction_history(tx)
    assert len(history) == 2
    # LIFO order
    assert history[0][0].name == "t2"
    assert history[1][0].name == "t1"

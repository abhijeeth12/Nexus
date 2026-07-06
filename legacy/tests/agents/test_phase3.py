"""Tests for Phase 3 components."""

import pytest
from typing import Any, Dict, List, Tuple

from core.interfaces.tool import ITool, SafetyTier
from core.interfaces.agent import IAgent
from core.models.tool_context import ExecutionResult, ToolContext
from engine.transaction import TransactionManager
from engine.execution_engine import ExecutionEngine
from agents.registry import CapabilityRegistry
from agents.orchestrator import Orchestrator
from agents.file_agent import FileAgent

class DummyTool(ITool):
    @property
    def name(self) -> str: return "dummy_tool"
    @property
    def description(self) -> str: return ""
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    @property
    def input_schema(self) -> Any: return None
    def validate(self, **kwargs: Any) -> bool: return True
    def execute(self, context: Any, **kwargs: Any) -> ExecutionResult:
        return ExecutionResult(success=True, output=kwargs.get("val"))
    def rollback(self, context: Any) -> ExecutionResult:
        return ExecutionResult(success=True)

class DummyAgent(IAgent):
    @property
    def name(self) -> str: return "dummy_agent"
    def get_capabilities(self) -> List[ITool]: return [DummyTool()]
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        return [(DummyTool(), instruction.get("params", {}))]

def test_capability_registry() -> None:
    registry = CapabilityRegistry()
    agent = DummyAgent()
    registry.register_agent(agent)
    
    assert registry.get_agent("dummy_agent") is not None
    assert registry.get_agent("missing") is None
    
    caps = registry.get_all_capabilities()
    assert "dummy_agent" in caps
    assert len(caps["dummy_agent"]) == 1
    assert caps["dummy_agent"][0].name == "dummy_tool"

def test_orchestrator_success() -> None:
    registry = CapabilityRegistry()
    registry.register_agent(DummyAgent())
    
    tm = TransactionManager()
    engine = ExecutionEngine(tm)
    orchestrator = Orchestrator(registry, engine)
    
    ctx = ToolContext(transaction_id="tx_1", working_directory=".")
    results = orchestrator.execute_instruction("dummy_agent", {"params": {"val": 42}}, ctx)
    
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].output == 42

def test_orchestrator_missing_agent() -> None:
    registry = CapabilityRegistry()
    tm = TransactionManager()
    engine = ExecutionEngine(tm)
    orchestrator = Orchestrator(registry, engine)
    
    ctx = ToolContext(transaction_id="tx_1", working_directory=".")
    results = orchestrator.execute_instruction("missing", {}, ctx)
    
    assert len(results) == 1
    assert results[0].success is False
    assert "not found" in str(results[0].error)

def test_file_agent_capabilities() -> None:
    agent = FileAgent()
    assert agent.name == "file_agent"
    caps = agent.get_capabilities()
    assert len(caps) == 6
    names = [c.name for c in caps]
    assert "read_file" in names
    assert "move_file" in names

def test_file_agent_handle_instruction() -> None:
    agent = FileAgent()
    calls = agent.handle_instruction({
        "intent": "move_file",
        "parameters": {"source": "a", "destination": "b"}
    })
    assert len(calls) == 1
    tool, kwargs = calls[0]
    assert tool.name == "move_file"
    assert kwargs["source"] == "a"

def test_file_agent_invalid_intent() -> None:
    agent = FileAgent()
    with pytest.raises(ValueError):
        agent.handle_instruction({"intent": "hack_mainframe"})

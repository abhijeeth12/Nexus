"""Test the core domain interfaces."""

import pytest
from typing import Any, Dict, List

from core.interfaces.tool import ITool
from core.interfaces.agent import IAgent
from core.interfaces.engine import IExecutionEngine
from core.interfaces.memory import IMemoryProvider
from core.models.tool_context import ToolContext, SafetyTier

def test_itool_is_abstract() -> None:
    """Verify ITool cannot be instantiated directly."""
    with pytest.raises(TypeError):
        ITool() # type: ignore

def test_iagent_is_abstract() -> None:
    """Verify IAgent cannot be instantiated directly."""
    with pytest.raises(TypeError):
        IAgent() # type: ignore

def test_iengine_is_abstract() -> None:
    """Verify IExecutionEngine cannot be instantiated directly."""
    with pytest.raises(TypeError):
        IExecutionEngine() # type: ignore

def test_imemory_is_abstract() -> None:
    """Verify IMemoryProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        IMemoryProvider() # type: ignore

def test_dummy_tool_instantiation() -> None:
    """Verify a properly implemented tool can be instantiated."""
    class DummyTool(ITool):
        @property
        def name(self) -> str: return "dummy"
        @property
        def description(self) -> str: return "desc"
        @property
        def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
        @property
        def input_schema(self) -> Any: return None
        
        def validate(self, **kwargs: Any) -> bool: return True
        def execute(self, context: Any, **kwargs: Any) -> Any: pass
        def rollback(self, context: Any) -> Any: pass
        
    dt = DummyTool()
    assert dt.name == "dummy"

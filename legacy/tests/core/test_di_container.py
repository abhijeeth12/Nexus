"""Tests for the Dependency Injection Container."""

import pytest
from typing import Any
from dependency_injector.errors import Error

from core.di.container import NexusContainer
from core.interfaces.engine import IExecutionEngine
from core.interfaces.tool import ITool
from core.models.tool_context import ExecutionResult

class MockExecutionEngine(IExecutionEngine):
    """A dummy execution engine for testing the DI container."""
    def submit(self, tool: ITool, **kwargs: Any) -> ExecutionResult:
        return ExecutionResult(success=True, output="mock_submit")
        
    def abort(self, transaction_id: str) -> bool:
        return True

def test_container_dependency_unresolved() -> None:
    """Verify that an unresolved dependency raises an error."""
    container = NexusContainer()
    
    # Trying to resolve an interface without overriding fails
    with pytest.raises(Error):
        container.execution_engine()

def test_container_dependency_override() -> None:
    """Verify that dependencies can be safely mocked and resolved."""
    container = NexusContainer()
    
    # Inject mock implementation
    container.execution_engine.override(MockExecutionEngine())
    
    engine = container.execution_engine()
    assert isinstance(engine, MockExecutionEngine)
    
    # Verify mock behavior
    res = engine.abort("tx_123")
    assert res is True

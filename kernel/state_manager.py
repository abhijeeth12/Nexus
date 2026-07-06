"""ObjectStore and HistoryStore default implementations."""

from core.interfaces.kernel import IObjectStore, IExecutionHistoryStore
from core.models.workflow_objects import WorkflowObject
from core.models.history import CapabilityExecution
from typing import Any, Dict, List, Optional
import threading

class InMemoryObjectStore(IObjectStore):
    """Thread-safe in-memory implementation for IObjectStore."""
    def __init__(self) -> None:
        self._objects: Dict[str, WorkflowObject] = {}
        self._lock = threading.Lock()
        
    def get_object(self, object_id: str) -> Optional[WorkflowObject]:
        with self._lock:
            return self._objects.get(object_id)
            
    def put_object(self, obj: WorkflowObject) -> None:
        with self._lock:
            self._objects[obj.object_id] = obj
            
    def list_objects(self, filter_args: Dict[str, Any] = None) -> List[WorkflowObject]:
        with self._lock:
            return list(self._objects.values())

    def clear(self) -> None:
        """Clear all objects from the store."""
        with self._lock:
            self._objects.clear()

class InMemoryHistoryStore(IExecutionHistoryStore):
    """Thread-safe in-memory implementation for IExecutionHistoryStore."""
    def __init__(self) -> None:
        self._executions: Dict[str, CapabilityExecution] = {}
        self._lock = threading.Lock()
        
    def record_execution(self, execution: CapabilityExecution) -> None:
        with self._lock:
            self._executions[execution.execution_id] = execution
            
    def get_execution(self, execution_id: str) -> Optional[CapabilityExecution]:
        with self._lock:
            return self._executions.get(execution_id)

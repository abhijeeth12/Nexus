"""Worker Pool and Resource Management."""

from core.interfaces.kernel import IWorkerPool, IResourceManager, IWorker, IObjectStore, IEventBus
from core.models.graph import TaskNode
from typing import Dict, Any, Optional
import threading
import logging
import uuid

logger = logging.getLogger(__name__)

class CapabilityContext:
    """Explicit context passed to capabilities. No global state access allowed."""
    def __init__(self, object_store: IObjectStore, workspace: str, cancellation_token: Any) -> None:
        self.object_store = object_store
        self.workspace = workspace
        self.cancellation_token = cancellation_token

class LocalWorkerPool(IWorkerPool):
    """Executes tasks in local background threads."""
    def __init__(self, executor: IWorker, event_bus: IEventBus) -> None:
        self.executor = executor
        self.event_bus = event_bus
        
    def dispatch(self, task: TaskNode) -> str:
        execution_id = str(uuid.uuid4())
        thread = threading.Thread(target=self._run_task, args=(task, execution_id))
        thread.start()
        return execution_id
        
    def _run_task(self, task: TaskNode, execution_id: str) -> None:
        try:
            # In a full system, CapabilityContext is injected here based on task requirements
            self.executor.execute(task, None)
        except Exception as e:
            logger.error(f"Worker failed on task {task.task_id}: {e}")

class LocalResourceManager(IResourceManager):
    """Mock resource manager that always grants resources."""
    def acquire(self, requirements: Dict[str, Any]) -> bool:
        return True
        
    def release(self, requirements: Dict[str, Any]) -> None:
        pass

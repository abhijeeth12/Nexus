"""Capability Executor."""

from core.interfaces.kernel import IWorker, ICapabilityRegistry, IEventBus, IObjectStore, IExecutionHistoryStore
from core.models.graph import TaskNode
from core.models.history import CapabilityExecution
from kernel.event_bus import BaseEvent
from typing import Any
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TaskCompletedEvent(BaseEvent):
    event_type: str = "TaskCompleted"
    
class TaskFailedEvent(BaseEvent):
    event_type: str = "TaskFailed"

class CapabilityExecutor(IWorker):
    """Orchestrates the Capability Lifecycle (Validate -> Prepare -> Execute -> Commit)."""
    
    def __init__(self, registry: ICapabilityRegistry, object_store: IObjectStore, history_store: IExecutionHistoryStore, event_bus: IEventBus, working_memory: dict = None) -> None:
        self.registry = registry
        self.object_store = object_store
        self.history_store = history_store
        self.event_bus = event_bus
        self.working_memory = working_memory if working_memory is not None else {}
        
    def execute(self, task: TaskNode, context: Any) -> Any:
        execution_id = task.task_id
        execution = CapabilityExecution(
            execution_id=execution_id,
            capability_name=task.capability_name,
            capability_version="1.0",
            status="RUNNING",
            inputs=task.inputs
        )
        self.history_store.record_execution(execution)
        
        try:
            # The Capability Lifecycle
            
            # 1. Resolve Plugin
            plugin = self.registry.get_plugin(task.capability_name)
            if not plugin:
                raise ValueError(f"Plugin not found for capability: {task.capability_name}")
            
            # 2. Prepare Context (Since Context is None in worker dispatch, we create CapabilityContext)
            # We inject the object store and workspace
            from kernel.worker import CapabilityContext
            import os
            cap_context = CapabilityContext(object_store=self.object_store, workspace=os.getcwd(), cancellation_token=None)
            
            # 3. Execute Core Logic
            output_objects = plugin.execute(cap_context, task.inputs)
            # 4. Commit Outputs to Provenance Graph
            if output_objects:
                committed_objects = []
                for obj in output_objects:
                    # WorkflowObjects are strictly immutable, so we create a copy to inject the execution_id
                    committed_obj = obj.model_copy(update={"producer_execution_id": execution_id})
                    self.object_store.put_object(committed_obj)
                    committed_objects.append(committed_obj)
                execution.outputs = [o.object_id for o in committed_objects]
            
            execution.status = "SUCCEEDED"
            execution.completed_at = datetime.now(timezone.utc)
            self.history_store.record_execution(execution)
            
            self.event_bus.publish(TaskCompletedEvent(metadata={"task_id": task.task_id, "execution_id": execution_id}))
            
        except Exception as e:
            execution.status = "FAILED"
            execution.exception = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            self.history_store.record_execution(execution)
            
            self.event_bus.publish(TaskFailedEvent(metadata={"task_id": task.task_id, "execution_id": execution_id, "error": str(e)}))

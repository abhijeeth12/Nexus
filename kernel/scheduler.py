"""Kernel Scheduler Subsystem."""

from core.interfaces.kernel import IScheduler, IEventBus, IObjectStore, IWorkerPool, IResourceManager
from core.models.graph import TaskGraph, TaskState, TaskNode
from kernel.event_bus import BaseEvent
import threading
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TaskStateChangeEvent(BaseEvent):
    event_type: str = "TaskStateChanged"
    task_id: str
    old_state: TaskState
    new_state: TaskState
    
class EventDrivenScheduler(IScheduler):
    """Reacts to events to evolve the executable Task Graph state."""
    
    def __init__(self, event_bus: IEventBus, object_store: IObjectStore, worker_pool: IWorkerPool, resource_manager: IResourceManager) -> None:
        self.event_bus = event_bus
        self.object_store = object_store
        self.worker_pool = worker_pool
        self.resource_manager = resource_manager
        
        self.graphs: Dict[str, TaskGraph] = {}
        self._lock = threading.Lock()
        
        # Subscribe to execution events
        self.event_bus.subscribe("TaskCompleted", self._on_task_completed)
        self.event_bus.subscribe("TaskFailed", self._on_task_failed)
        
    def submit_graph(self, executable_graph: TaskGraph) -> None:
        with self._lock:
            if executable_graph.workflow_id not in self.graphs:
                self.graphs[executable_graph.workflow_id] = executable_graph
            else:
                self.graphs[executable_graph.workflow_id].nodes.update(executable_graph.nodes)
                
            for node in executable_graph.nodes.values():
                self._transition(node, TaskState.WAITING)
                
        self.evaluate_readiness()
        
    def _transition(self, node: TaskNode, new_state: TaskState) -> None:
        old_state = node.state
        if old_state == new_state:
            return
        node.transition(new_state)
        self.event_bus.publish(TaskStateChangeEvent(task_id=node.task_id, old_state=old_state, new_state=new_state))
        
    def evaluate_readiness(self) -> None:
        """Evaluates constraints and moves tasks to Ready Queue."""
        with self._lock:
            for graph in self.graphs.values():
                for node in graph.nodes.values():
                    if node.state == TaskState.WAITING:
                        # 1. Check dependencies
                        ready = True
                        failed_dep = False
                        for dep_id in node.dependencies:
                            dep_node = graph.nodes.get(dep_id)
                            if not dep_node:
                                ready = False
                                break
                            if dep_node.state == TaskState.FAILED:
                                failed_dep = True
                                break
                            elif dep_node.state != TaskState.SUCCEEDED:
                                ready = False
                                break
                        
                        if failed_dep:
                            self._transition(node, TaskState.FAILED)
                            continue
                            
                        # 2. In a full engine, we verify required DataGraph objects exist here
                        
                        if ready:
                            self._transition(node, TaskState.READY)
                            
            # Dispatch Ready Tasks
            self._dispatch_ready_tasks()
            
    def _dispatch_ready_tasks(self) -> None:
        for graph in self.graphs.values():
            for node in graph.nodes.values():
                if node.state == TaskState.READY:
                    # Request resources
                    # if self.resource_manager.acquire(contract.resource_requirements):
                    self._transition(node, TaskState.RUNNING)
                    self.worker_pool.dispatch(node)
                    
    def _on_task_completed(self, event: BaseEvent) -> None:
        task_id = event.metadata.get("task_id")
        if not task_id: return
        
        with self._lock:
            for graph in self.graphs.values():
                if task_id in graph.nodes:
                    self._transition(graph.nodes[task_id], TaskState.SUCCEEDED)
                    break
        self.evaluate_readiness()
        
    def _on_task_failed(self, event: BaseEvent) -> None:
        task_id = event.metadata.get("task_id")
        if not task_id: return
        
        with self._lock:
            for graph in self.graphs.values():
                if task_id in graph.nodes:
                    # Apply retry policy here in the future
                    self._transition(graph.nodes[task_id], TaskState.FAILED)
                    break
                    
    def get_ready_tasks(self) -> List[Any]:
        # Utility if a polling worker model is used instead of push
        ready = []
        with self._lock:
            for graph in self.graphs.values():
                for node in graph.nodes.values():
                    if node.state == TaskState.READY:
                        ready.append(node)
        return ready

    def is_idle(self) -> bool:
        """Returns True if there are no WAITING, READY, or RUNNING tasks."""
        with self._lock:
            for graph in self.graphs.values():
                for node in graph.nodes.values():
                    if node.state in (TaskState.WAITING, TaskState.READY, TaskState.RUNNING):
                        return False
        return True

    def clear(self) -> None:
        """Clear all task graphs."""
        with self._lock:
            self.graphs.clear()

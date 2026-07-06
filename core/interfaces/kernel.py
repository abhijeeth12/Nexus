"""Core Kernel Interfaces for Nexus Workflow Operating System."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from datetime import datetime

class KernelEvent(ABC):
    """Base class for all system events."""
    event_type: str
    timestamp: datetime
    metadata: Dict[str, Any]

class IEventBus(ABC):
    """Central nervous system for decoupled event propagation."""
    
    @abstractmethod
    def publish(self, event: KernelEvent) -> None:
        pass
        
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        pass

class IObjectStore(ABC):
    """Manages the DataGraph (Provenance Graph) and WorkflowObjects."""
    
    @abstractmethod
    def get_object(self, object_id: str) -> Optional[Any]:
        pass
        
    @abstractmethod
    def put_object(self, obj: Any) -> None:
        pass
        
    @abstractmethod
    def list_objects(self, filter_args: Dict[str, Any] = None) -> List[Any]:
        pass

class IExecutionHistoryStore(ABC):
    """Permanent record of every capability execution."""
    
    @abstractmethod
    def record_execution(self, execution: Any) -> None:
        pass
        
    @abstractmethod
    def get_execution(self, execution_id: str) -> Optional[Any]:
        pass

class IScheduler(ABC):
    """State machine manager for TaskNodes."""
    
    @abstractmethod
    def submit_graph(self, executable_graph: Any) -> None:
        pass
        
    @abstractmethod
    def evaluate_readiness(self) -> None:
        """Evaluates constraints and moves tasks to Ready Queue."""
        pass
        
    @abstractmethod
    def get_ready_tasks(self) -> List[Any]:
        pass

class IWorker(ABC):
    """Executes a single capability in a sandboxed context."""
    
    @abstractmethod
    def execute(self, task: Any, context: Any) -> Any:
        pass

class IWorkerPool(ABC):
    """Manages scaling and dispatching of tasks to Workers."""
    
    @abstractmethod
    def dispatch(self, task: Any) -> str:
        """Dispatches a task and returns an execution ID."""
        pass

class IResourceManager(ABC):
    """Allocates system resources (CPU, Memory, Locks)."""
    
    @abstractmethod
    def acquire(self, requirements: Dict[str, Any]) -> bool:
        pass
        
    @abstractmethod
    def release(self, requirements: Dict[str, Any]) -> None:
        pass

class ICapabilityRegistry(ABC):
    """Plugin registry for Capability Contracts."""
    
    @abstractmethod
    def get_contract(self, capability_name: str) -> Optional[Any]:
        pass
        
    @abstractmethod
    def get_plugin(self, capability_name: str) -> Optional['ICapabilityPlugin']:
        pass
        
    @abstractmethod
    def load_plugins(self, path: str) -> None:
        pass

class ICapabilityPlugin(ABC):
    """Interface that every V2 Semantic Capability must implement."""
    
    @abstractmethod
    def get_contract(self) -> Any:
        pass
        
    @abstractmethod
    def execute(self, context: Any, inputs: Dict[str, Any]) -> List[Any]:
        """Executes the capability and returns a list of produced WorkflowObjects."""
        pass

class ICacheStore(ABC):
    """Semantic cache manager."""
    
    @abstractmethod
    def check_hit(self, cache_key: str) -> Optional[Any]:
        pass
        
    @abstractmethod
    def store_entry(self, cache_key: str, output_objects: List[str]) -> None:
        pass

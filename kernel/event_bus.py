"""Event Bus Subsystem for decoupled propagation."""

from core.interfaces.kernel import IEventBus, KernelEvent
from typing import Dict, List, Callable, Any
import threading
import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class BaseEvent(BaseModel, KernelEvent):
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EventBus(IEventBus):
    """Default local threading implementation of IEventBus."""
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[KernelEvent], None]]] = {}
        self._lock = threading.Lock()
        
    def publish(self, event: KernelEvent) -> None:
        with self._lock:
            handlers = self._subscribers.get(event.event_type, [])
            handlers = handlers + self._subscribers.get("*", [])
            
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler failed for {event.event_type}: {e}")
                
    def subscribe(self, event_type: str, handler: Callable[[KernelEvent], None]) -> None:
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

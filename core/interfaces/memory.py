"""Memory provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class IMemoryProvider(ABC):
    """Abstract interface for Memory Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the memory provider (e.g., 'sqlite', 'chroma')."""
        pass

    @abstractmethod
    def query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve context matching the query."""
        pass

    @abstractmethod
    def store(self, fact: Dict[str, Any]) -> bool:
        """Store a new fact or context."""
        pass

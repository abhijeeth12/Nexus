"""Planner interface."""

from abc import ABC, abstractmethod
from typing import Any
from core.models.instruction import GraphUpdate
from core.interfaces.kernel import ICapabilityRegistry

class IPlanner(ABC):
    """Abstract interface for the LLM reasoning engine."""
    
    @abstractmethod
    def plan(self, context: Any, registry: Any) -> GraphUpdate:
        """
        Generates a GraphUpdate based on the current context.
        """
        pass

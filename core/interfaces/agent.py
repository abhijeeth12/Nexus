"""Agent interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from core.interfaces.tool import ITool

class IAgent(ABC):
    """Abstract interface for a Specialized Agent."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the agent."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[ITool]:
        """Return a list of tools this agent provides."""
        pass

    @abstractmethod
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        """
        Translate a deterministic instruction from the Planner 
        into a list of configured Tools and their arguments to be executed.
        """
        pass

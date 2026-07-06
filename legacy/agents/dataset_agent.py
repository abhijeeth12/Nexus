"""Dataset Domain Agent."""

from typing import Any, Dict, List, Tuple
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool

from infrastructure.capabilities.dataset_operations import FilterDatasetCapability

class DatasetAgent(IAgent):
    """Domain-specific agent for handling dataset operations."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, ITool] = {
            "filter_dataset": FilterDatasetCapability(),
        }
        
    @property
    def name(self) -> str:
        return "dataset_domain"
        
    def get_capabilities(self) -> List[ITool]:
        return list(self._tools.values())
        
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        intent = instruction.get("intent")
        params = instruction.get("parameters", {})
        
        if not intent or intent not in self._tools:
            raise ValueError(f"Unknown or missing intent: {intent}")
            
        tool = self._tools[intent]
        return [(tool, params)]

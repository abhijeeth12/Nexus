"""File Agent."""

from typing import Any, Dict, List, Tuple
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool

from infrastructure.tools.file.read_tool import ReadFileTool
from infrastructure.capabilities.extension_discovery import ExtensionDiscoveryCapability

class FileAgent(IAgent):
    """Domain-specific agent for handling file system operations."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, ITool] = {
            "extension_search": ExtensionDiscoveryCapability(),
            # Exposing read_file as a capability to allow inspecting file contents
            "read_file": ReadFileTool()
        }
        
    @property
    def name(self) -> str:
        return "file_domain"
        
    def get_capabilities(self) -> List[ITool]:
        return list(self._tools.values())
        
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        """
        Expected instruction format:
        {
            "intent": "move_file",
            "parameters": {"source": "a.txt", "destination": "b.txt"}
        }
        """
        intent = instruction.get("intent")
        params = instruction.get("parameters", {})
        
        if not intent or intent not in self._tools:
            raise ValueError(f"Unknown or missing intent: {intent}")
            
        tool = self._tools[intent]
        return [(tool, params)]

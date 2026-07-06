"""Browser Agent."""

from typing import Any, Dict, List, Tuple
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool
from infrastructure.tools.browser.search_tool import WebSearchTool
from infrastructure.tools.browser.read_tool import ReadWebpageTool
from core.telemetry.logger import get_logger

logger = get_logger(__name__)

class BrowserAgent(IAgent):
    """Agent for web browsing and information retrieval."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, ITool] = {
            "web_search": WebSearchTool(),
            "read_webpage": ReadWebpageTool()
        }
        
    @property
    def name(self) -> str:
        return "browser_agent"
        
    @property
    def description(self) -> str:
        return "Agent capable of searching the web and reading webpages."
        
    def get_capabilities(self) -> List[ITool]:
        return list(self._tools.values())
        
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        intent = instruction.get("intent")
        params = instruction.get("parameters", {})
        
        if not intent or intent not in self._tools:
            logger.error(f"Unknown intent requested from BrowserAgent: {intent}")
            raise ValueError(f"Unknown intent: {intent}")
            
        tool = self._tools[intent]
        return [(tool, params)]

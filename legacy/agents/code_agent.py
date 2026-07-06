"""Code Agent."""

from typing import Any, Dict, List, Tuple
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool
from infrastructure.tools.code.edit_tool import EditFileTool
from infrastructure.tools.code.search_tool import ProjectSearchTool
from infrastructure.tools.code.ast_tool import ReadAstTool
from core.telemetry.logger import get_logger

logger = get_logger(__name__)

class CodeAgent(IAgent):
    """Agent for code manipulation and advanced refactoring."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, ITool] = {
            "edit_file": EditFileTool(),
            "project_search": ProjectSearchTool(),
            "read_ast": ReadAstTool()
        }
        
    @property
    def name(self) -> str:
        return "code_agent"
        
    @property
    def description(self) -> str:
        return "Agent capable of advanced code editing and search."
        
    def get_capabilities(self) -> List[ITool]:
        return list(self._tools.values())
        
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        intent = instruction.get("intent")
        params = instruction.get("parameters", {})
        
        if not intent or intent not in self._tools:
            logger.error(f"Unknown intent requested from CodeAgent: {intent}")
            raise ValueError(f"Unknown intent: {intent}")
            
        tool = self._tools[intent]
        return [(tool, params)]

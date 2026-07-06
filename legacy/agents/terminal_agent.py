"""Terminal Agent."""

from typing import Any, Dict, List, Tuple
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool
from infrastructure.tools.terminal.run_command_tool import RunCommandTool

class TerminalAgent(IAgent):
    """Domain-specific agent for handling terminal commands."""
    
    def __init__(self) -> None:
        from infrastructure.tools.terminal.structured_tools import FindDrivesTool, SearchDirectoryTool, LocatePythonTool, FindGitRepositoriesTool
        
        self._tools: Dict[str, ITool] = {
            "run_command": RunCommandTool(),
            "find_drives": FindDrivesTool(),
            "search_directory": SearchDirectoryTool(),
            "locate_python": LocatePythonTool(),
            "find_git_repositories": FindGitRepositoriesTool()
        }
        
    @property
    def name(self) -> str:
        return "terminal_agent"
        
    def get_capabilities(self) -> List[ITool]:
        return list(self._tools.values())
        
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        intent = instruction.get("intent")
        params = instruction.get("parameters", {})
        
        if not intent or intent not in self._tools:
            raise ValueError(f"Unknown or missing intent: {intent}")
            
        tool = self._tools[intent]
        return [(tool, params)]

"""OS Agent."""

from typing import Any, Dict, List, Tuple
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool
from infrastructure.tools.os.sysinfo_tool import SystemInfoTool
from infrastructure.tools.os.env_tool import EnvVarTool
from infrastructure.tools.os.process_tool import ProcessListTool
from core.telemetry.logger import get_logger

logger = get_logger(__name__)

class OSAgent(IAgent):
    """Agent for OS-level inspection and manipulation."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, ITool] = {
            "get_system_info": SystemInfoTool(),
            "env_vars": EnvVarTool(),
            "list_processes": ProcessListTool()
        }
        
    @property
    def name(self) -> str:
        return "os_agent"
        
    @property
    def description(self) -> str:
        return "Agent capable of reading system state, processes, and environment variables."
        
    def get_capabilities(self) -> List[ITool]:
        return list(self._tools.values())
        
    def handle_instruction(self, instruction: Dict[str, Any]) -> List[Tuple[ITool, Dict[str, Any]]]:
        intent = instruction.get("intent")
        params = instruction.get("parameters", {})
        
        if not intent or intent not in self._tools:
            logger.error(f"Unknown intent requested from OSAgent: {intent}")
            raise ValueError(f"Unknown intent: {intent}")
            
        tool = self._tools[intent]
        return [(tool, params)]

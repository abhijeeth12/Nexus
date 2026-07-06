"""System Information tool."""

import platform
import psutil
from typing import Any, Type
from pydantic import BaseModel

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class SystemInfoParams(BaseModel):
    """No parameters required."""
    pass

class SystemInfoTool(BaseTool):
    """Retrieves basic system information."""
    
    @property
    def name(self) -> str:
        return "get_system_info"
        
    @property
    def description(self) -> str:
        return "Gets system hardware, OS version, and basic resource usage."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return SystemInfoParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        try:
            info = {
                "OS": platform.system(),
                "Release": platform.release(),
                "Architecture": platform.machine(),
                "Processor": platform.processor(),
                "CPU_Cores": psutil.cpu_count(logical=False),
                "CPU_Logical_Cores": psutil.cpu_count(logical=True),
                "RAM_Total_GB": round(psutil.virtual_memory().total / (1024.**3), 2),
                "RAM_Available_GB": round(psutil.virtual_memory().available / (1024.**3), 2),
                "Disk_Total_GB": round(psutil.disk_usage('/').total / (1024.**3), 2),
                "Disk_Free_GB": round(psutil.disk_usage('/').free / (1024.**3), 2)
            }
            output = "\n".join([f"{k}: {v}" for k, v in info.items()])
            return ExecutionResult(success=True, output=output)
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to get system info: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")

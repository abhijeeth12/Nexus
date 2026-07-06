"""Run Command Tool."""

import subprocess
from typing import Any, Type
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class RunCommandInput(BaseModel):
    command: str = Field(description="The shell command to execute.")
    timeout: int = Field(default=30, description="Timeout in seconds.")

class RunCommandTool(BaseTool):
    """Executes a terminal command safely."""
    
    @property
    def name(self) -> str: return "run_command"
    
    @property
    def description(self) -> str: return "Executes a terminal command."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.SYSTEM_CHANGE
    
    @property
    def input_schema(self) -> Type[BaseModel]: return RunCommandInput
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: RunCommandInput = parsed_kwargs
        cmd = params.command
        to = params.timeout
        
        try:
            import platform
            if platform.system() == "Windows":
                exec_cmd = ["powershell", "-Command", cmd]
                shell_flag = False
            else:
                exec_cmd = cmd
                shell_flag = True
                
            result = subprocess.run(
                exec_cmd, 
                shell=shell_flag, 
                capture_output=True, 
                text=True, 
                timeout=to,
                cwd=context.working_directory
            )
            if result.returncode == 0:
                out_str = result.stdout.strip()
                if not out_str:
                    out_str = "Command executed successfully (no output)."
                return ExecutionResult(success=True, output=out_str)
            else:
                return ExecutionResult(success=False, error=f"Command failed with code {result.returncode}. Stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            return ExecutionResult(success=False, error=f"Command timed out after {to}s")
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Manual rollback required for arbitrary terminal commands.")

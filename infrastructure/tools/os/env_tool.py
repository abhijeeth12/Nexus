"""Environment Variables tool."""

import os
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class EnvVarParams(BaseModel):
    """Parameters for env vars."""
    action: str = Field(..., description="Action to perform: 'get' or 'list'")
    var_name: Optional[str] = Field(None, description="Name of the environment variable (only for 'get')")

class EnvVarTool(BaseTool):
    """Tool to read environment variables."""
    
    @property
    def name(self) -> str:
        return "env_vars"
        
    @property
    def description(self) -> str:
        return "Reads system environment variables."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return EnvVarParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: EnvVarParams = parsed_kwargs
        
        try:
            if params.action == "list":
                output = "\n".join([f"{k}={v}" for k, v in os.environ.items()])
                return ExecutionResult(success=True, output=output)
            elif params.action == "get":
                if not params.var_name:
                    return ExecutionResult(success=False, error="var_name is required for 'get' action.")
                val = os.environ.get(params.var_name)
                if val is not None:
                    return ExecutionResult(success=True, output=f"{params.var_name}={val}")
                return ExecutionResult(success=False, error=f"Environment variable '{params.var_name}' not found.")
            else:
                return ExecutionResult(success=False, error=f"Invalid action: {params.action}")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to read env vars: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")

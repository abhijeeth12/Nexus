"""Write File Tool."""

import os
from typing import Any, Type
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ToolContext, ExecutionResult, SafetyTier

class WriteFileInput(BaseModel):
    file_path: str = Field(description="The path to write to.")
    content: str = Field(description="The content to write.")
    overwrite: bool = Field(default=False, description="Whether to overwrite if file exists.")

class WriteFileTool(BaseTool):
    """Writes content to a file."""
    
    @property
    def name(self) -> str: return "write_file"
    
    @property
    def description(self) -> str: return "Writes textual content to a file."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.REVERSIBLE_CHANGE
    
    @property
    def input_schema(self) -> Type[BaseModel]: return WriteFileInput
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: WriteFileInput = parsed_kwargs
        p = params.file_path
        c = params.content
        ov = params.overwrite
        
        if os.path.exists(p) and not ov:
            return ExecutionResult(success=False, error=f"File exists and overwrite is false: {p}")
            
        # Store state for rollback
        context.state["file_path"] = p
        context.state["existed_before"] = os.path.exists(p)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                context.state["old_content"] = f.read()
                
        try:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(c)
            return ExecutionResult(success=True, output={"file_path": p, "bytes_written": len(c)})
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        p = context.state.get("file_path")
        if not p: return ExecutionResult(success=False, error="No file path provided in context")
        
        try:
            if context.state.get("existed_before"):
                # Restore old content
                old_c = context.state.get("old_content", "")
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(old_c)
            else:
                # Delete newly created file
                if os.path.exists(p):
                    os.remove(p)
            return ExecutionResult(success=True, output="Rolled back successfully")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Rollback failed: {e}")

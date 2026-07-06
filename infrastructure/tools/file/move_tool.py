"""Move file tool."""

import shutil
from pathlib import Path
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class MoveFileParams(BaseModel):
    """Parameters for moving a file."""
    source: str = Field(..., description="Path to the source file.")
    destination: str = Field(..., description="Path to the destination.")

class MoveFileTool(BaseTool):
    """Tool to move a file, supporting rollback."""
    
    def __init__(self) -> None:
        super().__init__()
        self._source: Optional[Path] = None
        self._destination: Optional[Path] = None
        
    @property
    def name(self) -> str:
        return "move_file"
        
    @property
    def description(self) -> str:
        return "Moves a file from source to destination."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.REVERSIBLE_CHANGE
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return MoveFileParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: MoveFileParams = parsed_kwargs
        src = Path(params.source)
        dst = Path(params.destination)
        
        if not src.is_absolute():
            src = Path(context.working_directory) / src
        if not dst.is_absolute():
            dst = Path(context.working_directory) / dst
            
        if not src.exists():
            return ExecutionResult(success=False, error=f"Source not found: {src}")
            
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_dir():
                dst = dst / src.name
                
            shutil.move(str(src), str(dst))
            self._source = src
            self._destination = dst
            return ExecutionResult(success=True, output=f"Moved to {dst}")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to move file: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        if not self._source or not self._destination:
            return ExecutionResult(success=False, error="No state to rollback.")
        if not self._destination.exists():
            return ExecutionResult(success=False, error=f"Cannot rollback, file not at {self._destination}")
            
        try:
            shutil.move(str(self._destination), str(self._source))
            return ExecutionResult(success=True, output="Rollback successful.")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Rollback failed: {e}")

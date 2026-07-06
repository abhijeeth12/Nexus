"""Delete file tool."""

import shutil
from pathlib import Path
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class DeleteFileParams(BaseModel):
    """Parameters for deleting a file."""
    file_path: str = Field(..., description="Path to the file to delete.")

class DeleteFileTool(BaseTool):
    """Tool to safely delete a file (moves to trash for rollback)."""
    
    def __init__(self) -> None:
        super().__init__()
        self._original_path: Optional[Path] = None
        self._trash_path: Optional[Path] = None
        
    @property
    def name(self) -> str:
        return "delete_file"
        
    @property
    def description(self) -> str:
        return "Safely deletes a file by moving it to a temporary trash for rollback capabilities."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.IRREVERSIBLE_CHANGE
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return DeleteFileParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: DeleteFileParams = parsed_kwargs
        path = Path(params.file_path)
        
        if not path.is_absolute():
            path = Path(context.working_directory) / path
            
        if not path.exists():
            return ExecutionResult(success=False, error=f"File not found: {path}")
            
        trash_dir = Path(context.working_directory) / ".nexus_trash" / context.transaction_id
        
        try:
            trash_dir.mkdir(parents=True, exist_ok=True)
            trash_path = trash_dir / path.name
            
            counter = 1
            while trash_path.exists():
                trash_path = trash_dir / f"{path.stem}_{counter}{path.suffix}"
                counter += 1
                
            shutil.move(str(path), str(trash_path))
            self._original_path = path
            self._trash_path = trash_path
            return ExecutionResult(success=True, output=f"File securely trashed.")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to delete file: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        if not self._original_path or not self._trash_path:
            return ExecutionResult(success=False, error="No state to rollback.")
        if not self._trash_path.exists():
            return ExecutionResult(success=False, error=f"Cannot rollback, trash missing at {self._trash_path}")
            
        try:
            shutil.move(str(self._trash_path), str(self._original_path))
            return ExecutionResult(success=True, output="Rollback successful.")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Rollback failed: {e}")

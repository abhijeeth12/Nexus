"""Edit file tool."""

import os
from pathlib import Path
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class EditFileParams(BaseModel):
    """Parameters for editing a file."""
    file_path: str = Field(..., description="Path to the file to edit.")
    target_content: str = Field(..., description="Exact string block to replace.")
    replacement_content: str = Field(..., description="New string block to insert.")

class EditFileTool(BaseTool):
    """Tool to safely edit a file by replacing a block of text."""
    
    def __init__(self) -> None:
        super().__init__()
        self._original_content: Optional[str] = None
        self._file_path: Optional[Path] = None
        
    @property
    def name(self) -> str:
        return "edit_file"
        
    @property
    def description(self) -> str:
        return "Replaces a specific block of text in a file with new content. Rollback restores the original file."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.REVERSIBLE_CHANGE  # Editing modifies state
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return EditFileParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: EditFileParams = parsed_kwargs
        path = Path(params.file_path)
        
        if not path.is_absolute():
            path = Path(context.working_directory) / path
            
        if not path.exists():
            return ExecutionResult(success=False, error=f"File not found: {path}")
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self._original_content = content
            self._file_path = path
            
            if params.target_content not in content:
                return ExecutionResult(success=False, error="Target content block not found in file.")
                
            new_content = content.replace(params.target_content, params.replacement_content, 1)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return ExecutionResult(success=True, output=f"File {path.name} edited successfully.")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to edit file: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        if not self._file_path or self._original_content is None:
            return ExecutionResult(success=False, error="No state to rollback.")
            
        try:
            with open(self._file_path, 'w', encoding='utf-8') as f:
                f.write(self._original_content)
            return ExecutionResult(success=True, output="File edit rolled back successfully.")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Rollback failed: {e}")

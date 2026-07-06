"""Project search tool."""

import os
import subprocess
from pathlib import Path
from typing import Any, Type
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class ProjectSearchParams(BaseModel):
    """Parameters for searching the project."""
    query: str = Field(..., description="The string or regex pattern to search for.")
    file_pattern: str = Field(default="*", description="Glob pattern for files to search in (e.g. *.py)")

class ProjectSearchTool(BaseTool):
    """Tool to search across the project codebase."""
    
    @property
    def name(self) -> str:
        return "project_search"
        
    @property
    def description(self) -> str:
        return "Searches for a specific text pattern across the project codebase."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.RESOURCE_INTENSIVE
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ProjectSearchParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ProjectSearchParams = parsed_kwargs
        
        # Use simple python walk or powershell/grep depending on OS, 
        # but to be OS agnostic, we can implement a fast python search.
        import fnmatch
        
        results = []
        base_dir = Path(context.working_directory)
        
        try:
            for root, dirs, files in os.walk(base_dir):
                # skip hidden dirs
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file_name in fnmatch.filter(files, params.file_pattern):
                    file_path = Path(root) / file_name
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if params.query in line:
                                    # Output format: file_path:line_num: line_content
                                    rel_path = file_path.relative_to(base_dir)
                                    results.append(f"{rel_path}:{i+1}: {line.strip()}")
                    except (UnicodeDecodeError, PermissionError):
                        continue
                        
            if not results:
                return ExecutionResult(success=True, output=f"No results found for '{params.query}'.")
                
            # Limit output to prevent massive context explosion
            if len(results) > 50:
                truncated_msg = f"\n...and {len(results) - 50} more matches."
                results = results[:50]
                results.append(truncated_msg)
                
            return ExecutionResult(success=True, output="\n".join(results))
        except Exception as e:
            return ExecutionResult(success=False, error=f"Search failed: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")

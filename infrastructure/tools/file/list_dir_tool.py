"""List Directory Tool."""

import os
from typing import Any, Type
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ToolContext, ExecutionResult, SafetyTier

class ListDirInput(BaseModel):
    path: str = Field(description="The directory path to list.")
    max_depth: int = Field(default=1, le=5, description="Maximum recursion depth for exploring subdirectories (1-5).")
    extensions: list[str] = Field(default_factory=list, description="Optional. List of extensions (e.g. ['.pdf', '.docx']) to filter files. If provided, ONLY files with these extensions and all directories will be shown.")
    directories_only: bool = Field(default=False, description="If true, returns only directories, hiding all files. Overrides extensions.")

class ListDirTool(BaseTool):
    """Lists the contents of a directory."""
    
    @property
    def name(self) -> str: return "list_dir"
    
    @property
    def description(self) -> str: return "Lists the contents of a directory."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    
    @property
    def input_schema(self) -> Type[BaseModel]: return ListDirInput
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ListDirInput = parsed_kwargs
        from pathlib import Path
        
        try:
            # If the LLM passes '/' on Windows, it wants to see the root drives
            if params.path.strip() in ("/", "\\", "global"):
                try:
                    import psutil
                    drives = {p.mountpoint: "[DRIVE]" for p in psutil.disk_partitions() if 'fixed' in p.opts.lower() or p.fstype}
                    drives["HINT"] = "To explore a drive, run list_dir again on the specific drive letter"
                    import json
                    return ExecutionResult(success=True, output=json.dumps(drives))
                except ImportError:
                    # Fallback if psutil is not available
                    import string
                    drives = {f"{d}:\\": "[DRIVE]" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")}
                    drives["HINT"] = "To explore a drive, run list_dir again on the specific drive letter"
                    import json
                    return ExecutionResult(success=True, output=json.dumps(drives))
            else:
                p = Path(params.path)
                if not p.is_absolute():
                    p = Path(context.working_directory) / p
                    
            target_dir = p.resolve()
            
            if not target_dir.exists() or not target_dir.is_dir():
                return ExecutionResult(success=False, error=f"Directory not found: {target_dir}")
            
            def build_tree(current_path, current_depth):
                if current_depth > params.max_depth:
                    return None
                try:
                    tree = {}
                    has_content = False
                    
                    # Normalize extensions (handle LLM over-escaping like \.pdf)
                    filter_exts = []
                    for ext in params.extensions:
                        clean_ext = ext.replace('\\', '').lower()
                        filter_exts.append(clean_ext if clean_ext.startswith('.') else f".{clean_ext}")
                    
                    for item in os.listdir(current_path):
                        # Skip massive hidden system folders
                        if item in ('$Recycle.Bin', 'System Volume Information', 'Windows'):
                            continue
                        
                        item_path = os.path.join(current_path, item)
                        if os.path.isdir(item_path):
                            if current_depth < params.max_depth:
                                subtree = build_tree(item_path, current_depth + 1)
                                # Only include directory if it has matching contents (when filtering)
                                if subtree or not (filter_exts or params.directories_only):
                                    tree[item] = subtree
                                    has_content = True
                            else:
                                tree[item] = "[DIR]"
                                has_content = True
                        else:
                            if params.directories_only:
                                continue
                                
                            if filter_exts:
                                ext = os.path.splitext(item)[1].lower()
                                if ext not in filter_exts:
                                    continue
                                    
                            tree[item] = "[FILE]"
                            has_content = True
                            
                    return tree if has_content else None

                except PermissionError:
                    return "[PERMISSION_DENIED]"
                except Exception as e:
                    return f"[ERROR: {str(e)}]"

            tree_output = build_tree(target_dir, 1)
            
            if not tree_output:
                return ExecutionResult(success=True, output="(Empty directory or Max Depth Reached)")
            import json
            final_output = {str(target_dir): tree_output}
            return ExecutionResult(success=True, output=json.dumps(final_output))

        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

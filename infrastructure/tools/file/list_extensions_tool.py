"""Tool for listing file extensions using the Extension Index Tree."""

import os
from typing import Any, Type, Optional
from pydantic import BaseModel, Field
import json

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier
from infrastructure.tools.file.extension_search_tool import _SHARED_EXTENSION_TREE

class ListExtensionsParams(BaseModel):
    search_root: Optional[str] = Field(default=None, description="Optional root path. Defaults to the current workspace.")

class ListExtensionsTool(BaseTool):
    """Lists all file extensions available in the system."""
    
    @property
    def name(self) -> str:
        return "list_extensions"
        
    @property
    def description(self) -> str:
        return "Returns a simple JSON array of all file extensions present in the specified directory or workspace (e.g., ['.py', '.git']). Use this to discover available file types with minimal context overhead."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ListExtensionsParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ListExtensionsParams = parsed_kwargs
        
        if params.search_root in ('/', '\\'):
            params.search_root = getattr(context, "working_directory", os.getcwd())
            
        root_to_scan = params.search_root or getattr(context, "working_directory", os.getcwd())
        
        # JIT populate the tree if empty
        if not _SHARED_EXTENSION_TREE.root.children:
            cache_path = os.path.join(getattr(context, "working_directory", os.getcwd()), ".nexus_extension_cache.json")
            if not _SHARED_EXTENSION_TREE.load_from_disk(cache_path):
                for root, dirs, files in os.walk(root_to_scan):
                    for d in dirs:
                        if d == ".git":
                            _SHARED_EXTENSION_TREE.add_path(os.path.join(root, d))
                    for f in files:
                        _SHARED_EXTENSION_TREE.add_path(os.path.join(root, f))
                # Save after building
                _SHARED_EXTENSION_TREE.save_to_disk(cache_path)
                    
        # If global search, return O(1) keys
        if not params.search_root or params.search_root == getattr(context, "working_directory", os.getcwd()):
            extensions = list(_SHARED_EXTENSION_TREE.root.children.keys())
        else:
            # Fallback to DFS search if scoped to a specific sub-directory
            extensions = []
            for ext, ext_node in _SHARED_EXTENSION_TREE.root.children.items():
                results = _SHARED_EXTENSION_TREE.search(ext, params.search_root)
                if results:
                    extensions.append(ext)
            
        return ExecutionResult(
            success=True,
            output=json.dumps(extensions)
        )

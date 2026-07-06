"""Tool for incredibly fast file discovery using the Extension Index Tree."""

import os
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier
from memory.storage.extension_tree import ExtensionIndexTree

_SHARED_EXTENSION_TREE = ExtensionIndexTree()

class ExtensionSearchParams(BaseModel):
    extension: str = Field(..., description="The file extension or special directory name to search for (e.g., '.py', '.git', '.md').")
    search_root: Optional[str] = Field(default=None, description="Optional root path. Defaults to the current workspace.")
    limit: int = Field(default=100, description="Maximum number of results to return. Limits output to prevent context window explosion.")

class ExtensionSearchTool(BaseTool):
    """Searches for files globally by their extension type using an optimized index tree."""
    
    @property
    def name(self) -> str:
        return "extension_search"
        
    @property
    def description(self) -> str:
        return "Rapidly discovers files or folders globally by their extension type (e.g., '.git', '.py') using an indexed tree structure."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ExtensionSearchParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ExtensionSearchParams = parsed_kwargs
        
        # 1. Parse comma or semicolon-separated extensions
        normalized_exts = params.extension.replace(';', ',')
        raw_exts = [e.strip() for e in normalized_exts.split(',') if e.strip()]
        clean_exts = []
        for e in raw_exts:
            if not e.startswith('.'):
                e = '.' + e
            clean_exts.append(e)
            
        if params.search_root in ('/', '\\', 'global', '') or params.search_root is None:
            params.search_root = "global"
            roots_to_scan = []
            try:
                import psutil
                for p in psutil.disk_partitions():
                    # Only scan fixed drives to avoid CD-ROMs/network drives hanging
                    if 'fixed' in p.opts.lower() or p.fstype:
                        roots_to_scan.append(p.mountpoint)
            except ImportError:
                roots_to_scan = [os.path.abspath(os.sep)]
        else:
            roots_to_scan = [params.search_root]
            
        # 2. JIT populate the tree if empty (Using Global Cache)
        if not _SHARED_EXTENSION_TREE.root.children:
            cache_path = os.path.expanduser("~/.nexus_global_cache.json")
            if not _SHARED_EXTENSION_TREE.load_from_disk(cache_path):
                # Cache miss: Build globally
                for scan_root in roots_to_scan:
                    for root, dirs, files in os.walk(scan_root):
                        # Prune Windows system and heavy hidden folders to speed up scanning
                        dirs[:] = [d for d in dirs if d not in ('$Recycle.Bin', 'System Volume Information', 'Windows')]
                        for d in dirs:
                            if d == ".git":
                                _SHARED_EXTENSION_TREE.add_path(os.path.join(root, d))
                        for f in files:
                            _SHARED_EXTENSION_TREE.add_path(os.path.join(root, f))
                _SHARED_EXTENSION_TREE.save_to_disk(cache_path)
                
        # 3. Query the DFS Tree for each extension
        all_results = []
        actual_search_root = None if params.search_root == "global" else params.search_root
        for ext in clean_exts:
            results = _SHARED_EXTENSION_TREE.search(ext, actual_search_root)
            all_results.extend(results)
            
        if not all_results:
            return ExecutionResult(success=True, output=f"No results found for extensions {params.extension}.")
            
        # 4. Truncate results to prevent context explosion
        all_results = all_results[:params.limit]
            
        # 5. Gather Metadata on leaf nodes (DFS result processing)
        import json
        output_objects = []
        for path, doc_id in all_results:
            try:
                stat = os.stat(path)
                meta = {
                    "path": path,
                    "size_bytes": stat.st_size,
                    "modified_timestamp": stat.st_mtime
                }
            except Exception:
                meta = {"path": path, "error": "Metadata retrieval failed"}
            output_objects.append(meta)
            
        # The executor will automatically push these objects into Shared Memory (ObjectStore)
        return ExecutionResult(success=True, output=json.dumps(output_objects))

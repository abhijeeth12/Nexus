"""Structured command templates for OS-independent planner operations."""

import platform
import subprocess
import os
from enum import Enum
from typing import Any, Type, Optional, List
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class FindDrivesParams(BaseModel):
    pass

class FindDrivesTool(BaseTool):
    """Discovers mounted filesystem drives."""
    
    @property
    def name(self) -> str: return "find_drives"
    
    @property
    def description(self) -> str: return "Returns a list of mounted filesystem drives available on this machine."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    
    @property
    def input_schema(self) -> Type[BaseModel]: return FindDrivesParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        sys = platform.system()
        try:
            if sys == "Windows":
                cmd = ["powershell", "-NoProfile", "-Command", "Get-PSDrive -PSProvider FileSystem | Select-Object -ExpandProperty Root"]
            else:
                cmd = ["df", "-h"]
                
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return ExecutionResult(success=True, output=res.stdout.strip())
        except subprocess.CalledProcessError as e:
            return ExecutionResult(success=False, error=e.stderr.strip() or str(e))

class SearchScope(str, Enum):
    ALL_DRIVES = "ALL_DRIVES"
    AUTO = "AUTO"
    USER_FILES = "USER_FILES"
    PROJECT_LOCATIONS = "PROJECT_LOCATIONS"
    CURRENT_WORKSPACE = "CURRENT_WORKSPACE"
    EXPLICIT_PATH = "EXPLICIT_PATH"

def _resolve_semantic_scope(scope: SearchScope, explicit_path: Optional[str], context: ToolContext) -> List[str]:
    sys = platform.system()
    if scope == SearchScope.EXPLICIT_PATH:
        return [explicit_path] if explicit_path else [context.working_directory]
    elif scope == SearchScope.CURRENT_WORKSPACE:
        return [context.working_directory]
    elif scope == SearchScope.USER_FILES:
        return [os.path.expanduser("~")]
    elif scope == SearchScope.PROJECT_LOCATIONS:
        # Default typical project locations
        if sys == "Windows":
            return [os.path.join(os.path.expanduser("~"), "Documents"), os.path.join(os.path.expanduser("~"), "Desktop"), "C:\\Projects"]
        return [os.path.join(os.path.expanduser("~"), "Documents"), os.path.join(os.path.expanduser("~"), "Projects"), "/var/www"]
    elif scope in (SearchScope.ALL_DRIVES, SearchScope.AUTO):
        if sys == "Windows":
            try:
                res = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-PSDrive -PSProvider FileSystem | Select-Object -ExpandProperty Root"], capture_output=True, text=True, check=True)
                return [d.strip() for d in res.stdout.strip().split('\n') if d.strip()]
            except:
                return ["C:\\"]
        return ["/"]
    return [context.working_directory]

class SearchDirectoryParams(BaseModel):
    target: str = Field(description="The specific file or directory name to search for (e.g., '.venv', 'package.json').")
    scope: SearchScope = Field(description="The semantic scope of the search.")
    explicit_path: Optional[str] = Field(default=None, description="The specific path to search, used only if scope is EXPLICIT_PATH.")
    exclude_system: bool = Field(default=True, description="Whether to exclude system and hidden folders.")

class SearchDirectoryTool(BaseTool):
    """Searches a directory tree for a specific file or folder name."""
    
    @property
    def name(self) -> str: return "search_directory"
    
    @property
    def description(self) -> str: return "Recursively searches a directory tree for a specific target name."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.RESOURCE_INTENSIVE
    
    @property
    def input_schema(self) -> Type[BaseModel]: return SearchDirectoryParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: SearchDirectoryParams = parsed_kwargs
        sys = platform.system()
        
        try:
            paths_to_search = _resolve_semantic_scope(params.scope, params.explicit_path, context)
            all_results = []
            
            for path in paths_to_search:
                if not os.path.exists(path):
                    continue
                if sys == "Windows":
                    ps_cmd = f"Get-ChildItem -Path '{path}' -Filter '{params.target}' -Recurse -ErrorAction SilentlyContinue"
                    if params.exclude_system:
                        ps_cmd += " -Attributes !Directory+!System,!Directory+!Hidden,Directory+!System,Directory+!Hidden"
                    ps_cmd += " | Select-Object -ExpandProperty FullName | Select-Object -First 50"
                    cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
                else:
                    cmd = ["find", path, "-name", params.target, "-print", "-quit"]
                    
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.stdout:
                    all_results.append(res.stdout.strip())
                    
            if all_results:
                return ExecutionResult(success=True, output="\n".join(all_results))
            return ExecutionResult(success=True, output="No results found.")
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

class LocatePythonParams(BaseModel):
    pass

class LocatePythonTool(BaseTool):
    """Locates the Python executable on the system."""
    
    @property
    def name(self) -> str: return "locate_python"
    
    @property
    def description(self) -> str: return "Finds the path to the python executable currently in use or installed."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    
    @property
    def input_schema(self) -> Type[BaseModel]: return LocatePythonParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        sys = platform.system()
        try:
            cmd = ["where", "python"] if sys == "Windows" else ["which", "python"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return ExecutionResult(success=True, output=res.stdout.strip())
        except subprocess.CalledProcessError:
            return ExecutionResult(success=False, error="Python executable not found in PATH.")

class FindGitRepositoriesParams(BaseModel):
    scope: SearchScope = Field(description="The semantic scope of the search.")
    explicit_path: Optional[str] = Field(default=None, description="The specific path to search, used only if scope is EXPLICIT_PATH.")

class FindGitRepositoriesTool(BaseTool):
    """Finds all git repositories within a scope."""
    
    @property
    def name(self) -> str: return "find_git_repositories"
    
    @property
    def description(self) -> str: return "Finds all git repositories (folders containing .git) within the specified path."
    
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.RESOURCE_INTENSIVE
    
    @property
    def input_schema(self) -> Type[BaseModel]: return FindGitRepositoriesParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: FindGitRepositoriesParams = parsed_kwargs
        sys = platform.system()
        
        try:
            paths_to_search = _resolve_semantic_scope(params.scope, params.explicit_path, context)
            all_results = []
            
            for path in paths_to_search:
                if not os.path.exists(path):
                    continue
                if sys == "Windows":
                    ps_cmd = f"Get-ChildItem -Path '{path}' -Filter '.git' -Recurse -Force -ErrorAction SilentlyContinue -Directory | Select-Object -ExpandProperty Parent | Select-Object -ExpandProperty FullName"
                    cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
                else:
                    cmd = ["find", path, "-type", "d", "-name", ".git"]
                    
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.stdout:
                    all_results.append(res.stdout.strip())
                    
            if all_results:
                return ExecutionResult(success=True, output="\n".join(all_results))
            return ExecutionResult(success=True, output="No repositories found.")
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

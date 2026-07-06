"""Process List tool."""

import psutil
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class ProcessListParams(BaseModel):
    """Parameters for listing processes."""
    limit: int = Field(default=20, description="Max number of processes to return (sorted by memory/cpu).")
    search_name: Optional[str] = Field(None, description="Optional name to filter processes by.")

class ProcessListTool(BaseTool):
    """Tool to inspect running processes."""
    
    @property
    def name(self) -> str:
        return "list_processes"
        
    @property
    def description(self) -> str:
        return "Lists currently running system processes."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ProcessListParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ProcessListParams = parsed_kwargs
        
        try:
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                info = proc.info
                if params.search_name:
                    name = info.get('name')
                    if name and params.search_name.lower() not in name.lower():
                        continue
                procs.append(info)
                
            # Sort by memory usage
            procs.sort(key=lambda p: p.get('memory_percent') or 0, reverse=True)
            
            output_lines = [f"{'PID':<8} {'NAME':<25} {'MEM%':<6} {'CPU%':<6}"]
            for p in procs[:params.limit]:
                mem = f"{p['memory_percent']:.1f}" if p['memory_percent'] else "0.0"
                cpu = f"{p['cpu_percent']:.1f}" if p['cpu_percent'] else "0.0"
                name = (p['name'][:22] + '...') if p['name'] and len(p['name']) > 25 else (p['name'] or 'N/A')
                output_lines.append(f"{p['pid']:<8} {name:<25} {mem:<6} {cpu:<6}")
                
            return ExecutionResult(success=True, output="\n".join(output_lines))
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to list processes: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")

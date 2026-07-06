"""Read webpage tool."""

import urllib.request
from typing import Any, Type
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class ReadWebpageParams(BaseModel):
    """Parameters for reading a webpage."""
    url: str = Field(..., description="URL to read")

class ReadWebpageTool(BaseTool):
    """Tool to extract text content from a URL."""
    
    @property
    def name(self) -> str:
        return "read_webpage"
        
    @property
    def description(self) -> str:
        return "Reads and extracts text from a remote webpage. ONLY for HTTP/HTTPS URLs. DO NOT use for local file paths or directories."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ReadWebpageParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ReadWebpageParams = parsed_kwargs
        
        try:
            req = urllib.request.Request(params.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            import re
            # Remove scripts and styles
            html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # Collapse whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Truncate if too long to prevent context explosion
            if len(text) > 8000:
                text = text[:8000] + "\n\n...[Content Truncated]..."
                
            return ExecutionResult(success=True, output=text)
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to read webpage: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")

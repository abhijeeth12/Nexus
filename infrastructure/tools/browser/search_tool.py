"""Web search tool."""

import urllib.request
import urllib.parse
import json
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class WebSearchParams(BaseModel):
    """Parameters for web search."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, description="Number of results to return")

class WebSearchTool(BaseTool):
    """Tool to search the web using a public API (DuckDuckGo Lite or equivalent)."""
    
    @property
    def name(self) -> str:
        return "web_search"
        
    @property
    def description(self) -> str:
        return "Searches the web for the given query and returns a list of URLs and snippets."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.RESOURCE_INTENSIVE
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return WebSearchParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: WebSearchParams = parsed_kwargs
        
        try:
            # Note: For prototype, we use an open search endpoint or mock if network blocked
            # We can use duckduckgo HTML search with a custom User-Agent
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(params.query)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                
            # Basic parsing without BeautifulSoup to avoid missing dependencies
            results = []
            import re
            # Extract links and snippets roughly
            links = re.findall(r'<a class="result__url" href="([^"]+)">([^<]+)</a>', html)
            snippets = re.findall(r'<a class="result__snippet[^>]+>(.*?)</a>', html)
            
            for i in range(min(params.limit, len(links))):
                url_href = links[i][0]
                # Duckduckgo wraps urls, extract real url if possible
                if "uddg=" in url_href:
                    url_href = urllib.parse.unquote(url_href.split("uddg=")[1].split("&")[0])
                
                snippet = snippets[i] if i < len(snippets) else ""
                # Strip HTML tags
                snippet = re.sub(r'<[^>]+>', '', snippet)
                results.append(f"{i+1}. URL: {url_href}\n   Snippet: {snippet.strip()}")
                
            if not results:
                return ExecutionResult(success=True, output="No search results found.")
                
            return ExecutionResult(success=True, output="\n\n".join(results))
        except Exception as e:
            return ExecutionResult(success=False, error=f"Web search failed: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")

"""Search file tool."""

import os
import math
import ollama
from pathlib import Path
from typing import Any, Type, Optional, List, Dict
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class SearchFileParams(BaseModel):
    """Parameters for searching files."""
    query: str = Field(default="", description="The string to search for in filenames. Also used as semantic query if RAG triggers. Leave empty to search all files.")
    extensions: list[str] = Field(default_factory=list, description="Optional. List of extensions (e.g. ['.pdf']) to filter files. If provided, ONLY matching files will be returned, which drastically speeds up search and prevents context explosion.")
    recursive: bool = Field(default=True, description="Whether to search recursively.")
    directory: str = Field(..., description="ABSOLUTE path of the directory to search in (e.g. C:\\Users\\user\\Documents). Do NOT omit this.")
    limit: int = Field(default=50, description="Max results before triggering Metadata RAG.")
    rag_top_k: int = Field(default=10, description="Top matches to return if Metadata RAG triggers.")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

class SearchFileTool(BaseTool):
    """Tool to search for files by name."""
    
    @property
    def name(self) -> str:
        return "search_files"
        
    @property
    def description(self) -> str:
        return "Searches for files matching a query in their name."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.RESOURCE_INTENSIVE
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return SearchFileParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: SearchFileParams = parsed_kwargs
        
        if params.directory in ('/', '\\', '.', '/path/to/workspace', 'A:\\path\\to\\workspace', 'a:\\path\\to\\workspace'):
            params.directory = getattr(context, "working_directory", os.getcwd())
            
        start_dir = params.directory or getattr(context, "working_directory", os.getcwd())
        path = Path(start_dir).resolve()
        
        if not path.is_absolute():
            path = Path(context.working_directory) / path
            
        if not path.exists() or not path.is_dir():
            return ExecutionResult(success=False, error=f"Invalid directory: {path}")
            
        results: set = set()
        try:
            normalized_query = params.query.replace(';', ',')
            patterns = [q.strip() for q in normalized_query.split(',') if q.strip()]
            
            if not patterns:
                patterns = ['*']
                
            # Normalize extensions (handle LLM over-escaping like \.pdf)
            filter_exts = []
            for ext in params.extensions:
                clean_ext = ext.replace('\\', '').lower()
                filter_exts.append(clean_ext if clean_ext.startswith('.') else f".{clean_ext}")
                
            for pat in patterns:
                search_pattern = pat
                if not ('*' in search_pattern or '?' in search_pattern):
                    search_pattern = f"*{search_pattern}*"
                search_pattern = search_pattern.replace('**', '*')
                
                generator = path.rglob(search_pattern) if params.recursive else path.glob(search_pattern)
                for p in generator:
                    if p.is_file():
                        if filter_exts:
                            file_ext = p.suffix.lower()
                            if file_ext not in filter_exts:
                                continue
                        results.add(str(p.absolute()))
            
            results = list(results)
            if len(results) <= params.limit:
                return ExecutionResult(success=True, output=results)
                
            # METADATA RAG TRIGGERED
            import json
            client = ollama.Client(host='http://127.0.0.1:11434')
            model_name = "nomic-embed-text"
            
            # Embed Query
            query_emb_resp = client.embeddings(model=model_name, prompt=params.query)
            query_vec = query_emb_resp.get("embedding")
            
            if not query_vec:
                return ExecutionResult(success=True, output=results[:params.limit]) # Fallback if ollama fails
                
            # Cap candidates to avoid insane wait times
            candidates = results[:500]
            scored_candidates = []
            
            for file_path in candidates:
                try:
                    stat = os.stat(file_path)
                    meta_text = f"File: {file_path} | Size: {stat.st_size} bytes"
                except Exception:
                    meta_text = f"File: {file_path}"
                    
                chunk_emb_resp = client.embeddings(model=model_name, prompt=meta_text)
                chunk_vec = chunk_emb_resp.get("embedding")
                if chunk_vec:
                    score = cosine_similarity(query_vec, chunk_vec)
                    scored_candidates.append({
                        "path": file_path,
                        "score": score,
                        "metadata": meta_text
                    })
                    
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)
            top_results = scored_candidates[:params.rag_top_k]
            
            output_formatted = [
                f"--- Result {i+1} (Score: {res['score']:.3f}) ---\n{res['metadata']}"
                for i, res in enumerate(top_results)
            ]
            
            output_formatted.insert(0, f"[METADATA RAG TRIGGERED] Found {len(results)} files. Semantically ranked top {params.rag_top_k} for '{params.query}':")
            
            return ExecutionResult(success=True, output="\n\n".join(output_formatted))
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to search files: {e}")

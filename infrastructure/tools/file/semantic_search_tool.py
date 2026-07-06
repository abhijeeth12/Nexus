"""Semantic search tool (RAG)."""

import os
import math
import ollama
from pathlib import Path
from typing import Any, Type, Optional, List, Dict
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class SemanticSearchParams(BaseModel):
    """Parameters for semantic search."""
    file_path: str = Field(..., description="The absolute or relative path to the file to search.")
    query: str = Field(..., description="The natural language query to search for.")
    top_k: int = Field(default=5, description="Number of top chunks to return.")
    chunk_size: int = Field(default=500, description="Size of each chunk in characters.")
    chunk_overlap: int = Field(default=100, description="Overlap between chunks in characters.")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

class SemanticSearchTool(BaseTool):
    """Tool to semantically search inside a file using RAG and vector embeddings."""
    
    @property
    def name(self) -> str:
        return "semantic_search"
        
    @property
    def description(self) -> str:
        return "Semantically searches a file for relevant context using RAG vector embeddings. Ideal for finding specific information in large files without reading the whole file."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.RESOURCE_INTENSIVE
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return SemanticSearchParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: SemanticSearchParams = parsed_kwargs
        
        path = Path(params.file_path)
        if not path.is_absolute():
            path = Path(getattr(context, "working_directory", os.getcwd())) / path
            
        if not path.exists() or not path.is_file():
            return ExecutionResult(success=False, error=f"File not found or is not a file: {path}")
            
        try:
            content = ""
            if path.suffix.lower() == '.pdf':
                try:
                    import PyPDF2
                    with open(path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                content += text + "\n"
                except Exception as pdf_e:
                    return ExecutionResult(success=False, error=f"Failed to parse PDF: {pdf_e}")
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
            if not content.strip():
                return ExecutionResult(success=False, error="File is empty or contains no extractable text.")
                
            # Basic text chunking
            chunks = []
            start = 0
            while start < len(content):
                end = start + params.chunk_size
                chunk_text = content[start:end]
                chunks.append(chunk_text)
                start += (params.chunk_size - params.chunk_overlap)
                
            client = ollama.Client(host='http://127.0.0.1:11434')
            model_name = "nomic-embed-text"
            
            # Embed Query
            query_emb_resp = client.embeddings(model=model_name, prompt=params.query)
            query_vec = query_emb_resp.get("embedding")
            if not query_vec:
                return ExecutionResult(success=False, error="Failed to generate query embedding.")
                
            # Embed Chunks and Score
            scored_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_emb_resp = client.embeddings(model=model_name, prompt=chunk)
                chunk_vec = chunk_emb_resp.get("embedding")
                if chunk_vec:
                    score = cosine_similarity(query_vec, chunk_vec)
                    scored_chunks.append({
                        "chunk_index": i,
                        "score": score,
                        "text": chunk
                    })
                    
            # Sort and get top K
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            top_results = scored_chunks[:params.top_k]
            
            output_formatted = [
                f"--- Result {i+1} (Score: {res['score']:.3f}) ---\n{res['text']}"
                for i, res in enumerate(top_results)
            ]
            
            return ExecutionResult(success=True, output="\n\n".join(output_formatted))
            
        except Exception as e:
            return ExecutionResult(success=False, error=f"Semantic search failed: {str(e)}")

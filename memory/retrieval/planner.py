"""Retrieval Planner."""

from typing import List, Dict, Any
from memory.interfaces.retrieval import IRetriever, IQueryAnalyzer

class BasicQueryAnalyzer(IQueryAnalyzer):
    """A basic query analyzer using keyword heuristics."""
    def analyze(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        return {
            "needs_metadata": True, # Metadata is typically always useful
            "needs_keyword": ("." in q or "find" in q),
            "needs_dense": ("concept" in q or "about" in q or "discussing" in q),
            "needs_graph": ("related" in q or "folder" in q or "project" in q)
        }

class RetrievalPlanner:
    """Analyzes a user query and selects the necessary retrieval strategies."""
    
    def __init__(self, available_retrievers: List[IRetriever], analyzer: IQueryAnalyzer) -> None:
        self._retrievers = {r.name: r for r in available_retrievers}
        self._analyzer = analyzer
        
    def plan_retrieval(self, query: str) -> List[IRetriever]:
        analysis = self._analyzer.analyze(query)
        selected: List[IRetriever] = []
        
        if analysis.get("needs_metadata") and "metadata" in self._retrievers:
            selected.append(self._retrievers["metadata"])
        if analysis.get("needs_keyword") and "keyword" in self._retrievers:
            selected.append(self._retrievers["keyword"])
        if analysis.get("needs_dense") and "dense" in self._retrievers:
            selected.append(self._retrievers["dense"])
        if analysis.get("needs_graph") and "graph" in self._retrievers:
            selected.append(self._retrievers["graph"])
            
        if not selected:
            default_retrievers = [r for name, r in self._retrievers.items() if name in ("dense", "metadata")]
            return default_retrievers if default_retrievers else list(self._retrievers.values())
            
        return selected

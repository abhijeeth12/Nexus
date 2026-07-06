"""Knowledge Retrieval Engine."""

from typing import List

from memory.interfaces.retrieval import IRetriever, IRankFusionStrategy
from memory.retrieval.planner import RetrievalPlanner
from memory.models import Candidate

class RetrievalEngine:
    """
    Coordinates RetrievalPlanner, executes selected IRetrievers,
    and merges the results via IRankFusionStrategy.
    """
    
    def __init__(self, planner: RetrievalPlanner, fusion_strategy: IRankFusionStrategy) -> None:
        self._planner = planner
        self._fusion = fusion_strategy
        
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]:
        """Executes the full retrieval flow returning rank-fused candidates."""
        retrievers = self._planner.plan_retrieval(query)
        
        candidate_lists: List[List[Candidate]] = []
        for retriever in retrievers:
            try:
                candidates = retriever.retrieve(query, limit=limit)
                if candidates:
                    candidate_lists.append(candidates)
            except Exception:
                pass
                
        return self._fusion.fuse(candidate_lists, limit)

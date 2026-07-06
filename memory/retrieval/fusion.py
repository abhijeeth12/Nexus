"""Rank Fusion Strategies."""

from typing import List, Dict
from memory.interfaces.retrieval import IRankFusionStrategy
from memory.models import Candidate

class ReciprocalRankFusion(IRankFusionStrategy):
    """
    Implements Reciprocal Rank Fusion (RRF).
    Scores are assigned based on the rank of the candidate in each list.
    """
    def __init__(self, k: int = 60) -> None:
        self.k = k

    def fuse(self, candidate_lists: List[List[Candidate]], limit: int) -> List[Candidate]:
        scores: Dict[str, float] = {}
        candidate_map: Dict[str, Candidate] = {}
        
        for clist in candidate_lists:
            for rank, candidate in enumerate(clist):
                chunk_id = candidate.chunk.id
                if chunk_id not in candidate_map:
                    candidate_map[chunk_id] = candidate
                    scores[chunk_id] = 0.0
                scores[chunk_id] += 1.0 / (self.k + rank + 1)
                
        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
        return [candidate_map[cid] for cid in sorted_ids[:limit]]

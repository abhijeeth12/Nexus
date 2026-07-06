"""Context Builder."""

from typing import List
from memory.interfaces.retrieval import IContextBuilder
from memory.models import Candidate

class DefaultContextBuilder(IContextBuilder):
    """
    Expands Context and formats output.
    Future: Use Graph/Metadata stores to pull sibling chunks and parent sections.
    """
    def build_context(self, candidates: List[Candidate]) -> str:
        blocks = []
        for rank, cand in enumerate(candidates):
            source = cand.retrieval_source
            content = cand.chunk.content
            blocks.append(f"[Source: {source} | Rank: {rank+1}]\n{content}\n")
        return "\n".join(blocks)

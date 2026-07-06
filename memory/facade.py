"""Memory Service Facade."""

from core.interfaces.knowledge import IKnowledgeRetrievalService
from memory.retrieval.engine import RetrievalEngine
from memory.interfaces.retrieval import IContextBuilder

class KnowledgeRetrievalService(IKnowledgeRetrievalService):
    """
    Concrete implementation of IKnowledgeRetrievalService.
    Wraps the internal RetrievalEngine to provide formatted context to the Orchestration layer.
    """
    
    def __init__(self, retrieval_engine: RetrievalEngine, context_builder: IContextBuilder) -> None:
        self._engine = retrieval_engine
        self._context_builder = context_builder
        
    def retrieve_context(self, query: str) -> str:
        # Retrieve candidates via the multi-strategy Rank Fusion engine
        candidates = self._engine.retrieve(query)
        # Build the final token-optimized context string
        return self._context_builder.build_context(candidates)

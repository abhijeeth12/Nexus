"""Knowledge Retrieval Abstraction."""

from abc import ABC, abstractmethod

class IKnowledgeRetrievalService(ABC):
    """
    Decoupled interface for retrieving formatted context from the Memory subsystem.
    The Planner depends on this, remaining entirely unaware of underlying
    retrieval strategies (Vector, Graph, Keyword).
    """
    
    @abstractmethod
    def retrieve_context(self, query: str) -> str:
        """Retrieves and formats relevant context for a given query."""
        pass

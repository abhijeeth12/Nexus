"""Memory Service Interface."""

from abc import ABC, abstractmethod
from typing import List
from memory.interfaces.storage import ISessionStore
from memory.models import Document, Chunk, Resource

class IMemoryService(ISessionStore, ABC):
    """Facade for the entire Memory subsystem."""
    
    @abstractmethod
    def store_document(self, document: Document, chunks: List[Chunk]) -> bool:
        """Stores a document and its chunks in the underlying storage providers."""
        pass
        
    @abstractmethod
    def store_resource_metadata(self, resource: Resource) -> bool:
        """Stores only the resource metadata. Useful when embeddings fail."""
        pass

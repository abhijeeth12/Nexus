"""Ingestion pipeline interfaces."""

from abc import ABC, abstractmethod
from typing import List

from memory.models import Resource, Document, Chunk

class IParser(ABC):
    """Converts a raw Resource into an indexable Document."""
    
    @abstractmethod
    def parse(self, resource: Resource) -> Document:
        pass

class IChunker(ABC):
    """Splits a Document into semantic Chunks."""
    
    @abstractmethod
    def chunk(self, document: Document) -> List[Chunk]:
        pass

class IEmbeddingProvider(ABC):
    """Generates embeddings for text, completely independent of storage."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass

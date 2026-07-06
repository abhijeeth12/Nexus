"""Storage backend interfaces."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from memory.models import Chunk, Document

class IVectorStore(ABC):
    """Interface for Vector Storage (e.g., Chroma, Qdrant). Does NOT generate embeddings."""
    @abstractmethod
    def store_chunks(self, chunks: List[Chunk]) -> bool: pass
    @abstractmethod
    def delete_chunks(self, chunk_ids: List[str]) -> bool: pass
    @abstractmethod
    def similarity_search(self, query_embedding: List[float], limit: int = 5) -> List[Chunk]: pass

class IGraphStore(ABC):
    """Interface for Graph Storage (e.g., NetworkX, Neo4j). Stores relationships."""
    @abstractmethod
    def add_node(self, node_id: str, metadata: Dict[str, Any]) -> None: pass
    @abstractmethod
    def add_edge(self, source_id: str, target_id: str, relationship: str) -> None: pass
    @abstractmethod
    def get_neighbors(self, node_id: str) -> List[str]: pass
    @abstractmethod
    def get_node_metadata(self, node_id: str) -> Dict[str, Any]: pass

class IMetadataStore(ABC):
    """Interface for Metadata Storage."""
    @abstractmethod
    def get_metadata(self, document_id: str) -> Dict[str, Any]: pass
    @abstractmethod
    def query_by_metadata(self, filters: Dict[str, Any]) -> List[Document]: pass

class IKeywordIndex(ABC):
    """Interface for exact Keyword Retrieval."""
    @abstractmethod
    def search(self, keyword: str, limit: int = 5) -> List[Chunk]: pass

class ISessionStore(ABC):
    """Interface for Session State and Execution History."""
    @abstractmethod
    def store_session(self, session_id: str, metadata: Dict[str, Any]) -> None: pass
    @abstractmethod
    def store_interaction(self, interaction_data: Dict[str, Any]) -> None: pass
    @abstractmethod
    def store_transaction(self, transaction_data: Dict[str, Any]) -> None: pass
    @abstractmethod
    def get_recent_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]: pass

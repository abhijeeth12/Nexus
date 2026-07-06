"""Memory Service implementation."""

import logging
from typing import List, Dict, Any

from memory.interfaces.memory_service import IMemoryService
from memory.interfaces.storage import IVectorStore, IGraphStore, ISessionStore
from core.interfaces.memory import IMemoryProvider
from memory.models import Document, Chunk, Resource

logger = logging.getLogger(__name__)

class MemoryService(IMemoryService, ISessionStore):
    """Orchestrates storing data across different storage backends."""
    
    def __init__(self, vector_store: IVectorStore, graph_store: IGraphStore, short_term_memory: IMemoryProvider) -> None:
        self._vector_store = vector_store
        self._graph_store = graph_store
        self._short_term_memory = short_term_memory
        
    def store_document(self, document: Document, chunks: List[Chunk]) -> bool:
        # Store in vector store (if available)
        v_success = True
        if self._vector_store:
            try:
                v_success = self._vector_store.store_chunks(chunks)
            except Exception as e:
                logger.error(f"Failed to store chunks in vector store: {e}")
                v_success = False
                
        # Store in graph store
        try:
            self._graph_store.add_node(document.id, {"type": "document", "resource_id": document.resource_id, "version": document.version, **document.metadata})
            for i, chunk in enumerate(chunks):
                self._graph_store.add_node(chunk.id, {"type": "chunk", "document_id": document.id, "index": i})
                self._graph_store.add_edge(chunk.id, document.id, "part_of")
                if i > 0:
                    self._graph_store.add_edge(chunks[i-1].id, chunk.id, "next")
        except Exception as e:
            logger.error(f"Failed to update graph store for document {document.id}: {e}")
            
        # Store in short term memory (SQLite) for exact keyword search
        for chunk in chunks:
            self._short_term_memory.store({
                "content": chunk.content,
                "metadata": {"chunk_id": chunk.id, "document_id": document.id, **chunk.metadata}
            })
            
        return v_success

    def store_resource_metadata(self, resource: Resource) -> bool:
        try:
            self._graph_store.add_node(resource.id, {"type": "resource", "resource_type": resource.resource_type, "checksum": resource.checksum})
            self._short_term_memory.store({
                "content": f"Resource discovered: {resource.id} of type {resource.resource_type}",
                "metadata": {"resource_id": resource.id, **resource.metadata}
            })
            return True
        except Exception as e:
            logger.error(f"Failed to store resource metadata: {e}")
            return False

    def store_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        if isinstance(self._short_term_memory, ISessionStore):
            self._short_term_memory.store_session(session_id, metadata)
            
    def store_interaction(self, interaction_data: Dict[str, Any]) -> None:
        if isinstance(self._short_term_memory, ISessionStore):
            self._short_term_memory.store_interaction(interaction_data)
            
    def store_transaction(self, transaction_data: Dict[str, Any]) -> None:
        if isinstance(self._short_term_memory, ISessionStore):
            self._short_term_memory.store_transaction(transaction_data)
            
    def get_recent_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        if isinstance(self._short_term_memory, ISessionStore):
            return self._short_term_memory.get_recent_history(session_id, limit)
        return []

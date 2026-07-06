"""Core Retrievers."""

from typing import List, Dict, Any
from memory.interfaces.retrieval import IRetriever
from memory.interfaces.storage import IMetadataStore, IKeywordIndex
from memory.models import Candidate, Chunk, Document

class KeywordRetriever(IRetriever):
    """Retrieves chunks using exact keyword matching via an index."""
    
    def __init__(self, index: IKeywordIndex) -> None:
        self._index = index
        
    @property
    def name(self) -> str: return "keyword"
    
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]:
        chunks = self._index.search(query, limit=limit)
        candidates = []
        for c in chunks:
            candidates.append(Candidate(
                chunk=c,
                retrieval_score=1.0, # exact match gets high score
                retrieval_source=self.name
            ))
        return candidates

class MetadataRetriever(IRetriever):
    """Retrieves documents based on metadata filters."""
    
    def __init__(self, store: IMetadataStore) -> None:
        self._store = store
        
    @property
    def name(self) -> str: return "metadata"
    
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]:
        # In a complete implementation, IQueryAnalyzer would extract exact dictionary filters.
        # For now, we simulate a basic keyword extraction mapped to metadata.
        # This allows us to satisfy the interface without a full NLP parser.
        filters = {"_query_hint": query} 
        documents = self._store.query_by_metadata(filters)[:limit]
        
        candidates = []
        for d in documents:
            # We return a synthetic chunk to represent the document's metadata match
            synthetic_chunk = Chunk(
                id=f"{d.id}#meta",
                document_id=d.id,
                content=f"Metadata match for Document: {d.metadata.get('filename', d.id)}"
            )
            candidates.append(Candidate(
                document=d,
                chunk=synthetic_chunk,
                retrieval_score=1.0,
                retrieval_source=self.name,
                metadata=d.metadata
            ))
        return candidates

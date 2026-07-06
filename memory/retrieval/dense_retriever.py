"""Dense Retriever."""

from typing import List

from memory.interfaces.retrieval import IRetriever
from memory.interfaces.storage import IVectorStore
from memory.interfaces.ingestion import IEmbeddingProvider
from memory.models import Candidate

class DenseRetriever(IRetriever):
    """Semantic similarity search utilizing a Vector Store and Embedding Provider."""
    
    def __init__(self, store: IVectorStore, embedding_provider: IEmbeddingProvider) -> None:
        self._store = store
        self._embedder = embedding_provider
        
    @property
    def name(self) -> str: return "dense"
    
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]:
        query_embedding = self._embedder.generate_embedding(query)
        chunks = self._store.similarity_search(query_embedding, limit=limit)
        
        candidates = []
        for c in chunks:
            candidates.append(Candidate(
                chunk=c,
                retrieval_score=0.9, # Distance could be integrated here if the vector store returns it
                retrieval_source=self.name,
                retrieval_evidence={"semantic_match": True}
            ))
        return candidates

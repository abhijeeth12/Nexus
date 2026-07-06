"""Chroma Vector Store."""

import chromadb
from typing import List

from memory.interfaces.storage import IVectorStore
from memory.models import Chunk

class ChromaVectorStore(IVectorStore):
    """Concrete implementation of IVectorStore using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./chroma_db") -> None:
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection("nexus_chunks")
        
    def store_chunks(self, chunks: List[Chunk]) -> bool:
        if not chunks:
            return True
            
        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        embeddings = [c.embedding for c in chunks] if chunks[0].embedding else None
        
        try:
            if embeddings:
                self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings) # type: ignore
            else:
                self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas) # type: ignore
            return True
        except Exception:
            return False

    def delete_chunks(self, chunk_ids: List[str]) -> bool:
        if not chunk_ids:
            return True
            
        try:
            self._collection.delete(ids=chunk_ids)
            return True
        except Exception:
            return False

    def similarity_search(self, query_embedding: List[float], limit: int = 5) -> List[Chunk]:
        try:
            results = self._collection.query(query_embeddings=[query_embedding], n_results=limit) # type: ignore
        except Exception:
            return []
            
        chunks: List[Chunk] = []
        if not results.get("ids") or not results["ids"][0]: # type: ignore
            return chunks
            
        # Chroma returns lists of lists for multiple queries. We only did one query.
        ids_list = results["ids"][0] # type: ignore
        docs_list = results["documents"][0] if results.get("documents") else [""] * len(ids_list) # type: ignore
        meta_list = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids_list) # type: ignore
        
        for i in range(len(ids_list)):
            chunk_id = ids_list[i]
            content = docs_list[i] if docs_list[i] is not None else ""
            metadata = meta_list[i] if meta_list[i] is not None else {}
            
            meta_dict = dict(metadata) if isinstance(metadata, dict) else {}
            doc_id = str(meta_dict.get("document_id", "unknown"))
            chunks.append(Chunk(id=str(chunk_id), document_id=doc_id, content=str(content), metadata=meta_dict))
            
        return chunks

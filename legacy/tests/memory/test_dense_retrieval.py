"""Tests for Dense Retrieval (Milestone 5)."""

import pytest
from typing import List

from memory.models import Chunk, Candidate
from memory.interfaces.storage import IVectorStore
from memory.interfaces.ingestion import IEmbeddingProvider
from memory.retrieval.dense_retriever import DenseRetriever

class MockVectorStore(IVectorStore):
    def store_chunks(self, chunks: List[Chunk]) -> bool: return True
    def delete_chunks(self, chunk_ids: List[str]) -> bool: return True
    def similarity_search(self, query_embedding: List[float], limit: int = 5) -> List[Chunk]:
        return [Chunk(id="c1", document_id="d1", content="mock semantic match")]

class MockEmbeddingProvider(IEmbeddingProvider):
    def generate_embedding(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3]]

def test_dense_retriever() -> None:
    store = MockVectorStore()
    embedder = MockEmbeddingProvider()
    retriever = DenseRetriever(store, embedder)
    
    candidates = retriever.retrieve("tell me about operating systems", limit=2)
    assert len(candidates) == 1
    assert candidates[0].retrieval_source == "dense"
    assert candidates[0].retrieval_evidence.get("semantic_match") is True
    assert candidates[0].chunk.content == "mock semantic match"

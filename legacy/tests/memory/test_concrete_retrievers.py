"""Tests for Milestone 4 Concrete Retrievers."""

import pytest
from typing import Dict, Any, List
from memory.models import Document, Chunk
from memory.interfaces.storage import IMetadataStore, IKeywordIndex
from memory.retrieval.retrievers import MetadataRetriever, KeywordRetriever

class MockMetadataStore(IMetadataStore):
    def get_metadata(self, document_id: str) -> Dict[str, Any]:
        return {}
    def query_by_metadata(self, filters: Dict[str, Any]) -> List[Document]:
        return [Document(id="d1", resource_id="r1", content="", metadata={"filename": "invoice.pdf"})]

class MockKeywordIndex(IKeywordIndex):
    def search(self, keyword: str, limit: int = 5) -> List[Chunk]:
        return [Chunk(id="c1", document_id="d1", content="Exact match found!")]

def test_metadata_retriever() -> None:
    store = MockMetadataStore()
    retriever = MetadataRetriever(store)
    
    candidates = retriever.retrieve("find invoice.pdf")
    assert len(candidates) == 1
    assert candidates[0].retrieval_source == "metadata"
    assert candidates[0].document is not None
    assert candidates[0].document.metadata["filename"] == "invoice.pdf"

def test_keyword_retriever() -> None:
    index = MockKeywordIndex()
    retriever = KeywordRetriever(index)
    
    candidates = retriever.retrieve("match")
    assert len(candidates) == 1
    assert candidates[0].retrieval_source == "keyword"
    assert candidates[0].chunk.content == "Exact match found!"

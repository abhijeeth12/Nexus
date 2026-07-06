"""Tests for Graph Retrieval (Milestone 6)."""

import pytest
from typing import List, Dict, Any

from memory.models import Chunk, Candidate
from memory.interfaces.storage import IGraphStore
from memory.retrieval.graph_retriever import GraphRetriever
from memory.providers.networkx_store import NetworkXGraphStore

def test_networkx_graph_store() -> None:
    store = NetworkXGraphStore()
    
    store.add_node("doc1", {"type": "document", "name": "invoice.pdf"})
    store.add_node("folder1", {"type": "folder", "name": "finance"})
    
    store.add_edge("folder1", "doc1", relationship="contains")
    
    neighbors = store.get_neighbors("doc1")
    assert "folder1" in neighbors
    
    meta = store.get_node_metadata("doc1")
    assert meta["name"] == "invoice.pdf"

def test_graph_retriever() -> None:
    store = NetworkXGraphStore()
    retriever = GraphRetriever(store)
    
    candidates = retriever.retrieve("find related items", limit=5)
    assert isinstance(candidates, list)
    # Returns empty for now because we haven't wired up seed node extraction

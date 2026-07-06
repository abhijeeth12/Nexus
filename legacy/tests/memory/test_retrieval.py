"""Tests for the Knowledge Retrieval Engine."""

import pytest
from typing import List

from memory.models import Chunk, Candidate
from memory.interfaces.retrieval import IRetriever
from memory.retrieval.planner import RetrievalPlanner, BasicQueryAnalyzer
from memory.retrieval.engine import RetrievalEngine
from memory.retrieval.fusion import ReciprocalRankFusion
from memory.retrieval.context import DefaultContextBuilder

class DummyMetadataRetriever(IRetriever):
    @property
    def name(self) -> str: return "metadata"
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]:
        chunk = Chunk(id="c1", document_id="d1", content="metadata_result")
        return [Candidate(chunk=chunk, retrieval_score=1.0, retrieval_source="metadata")]

class DummyDenseRetriever(IRetriever):
    @property
    def name(self) -> str: return "dense"
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]:
        chunk = Chunk(id="c2", document_id="d2", content="dense_result")
        return [Candidate(chunk=chunk, retrieval_score=0.9, retrieval_source="dense")]

def test_retrieval_planner() -> None:
    analyzer = BasicQueryAnalyzer()
    planner = RetrievalPlanner([DummyMetadataRetriever(), DummyDenseRetriever()], analyzer)
    
    plan = planner.plan_retrieval("concept about attention")
    names = [r.name for r in plan]
    assert "metadata" in names
    assert "dense" in names

def test_retrieval_engine_and_fusion() -> None:
    analyzer = BasicQueryAnalyzer()
    planner = RetrievalPlanner([DummyMetadataRetriever(), DummyDenseRetriever()], analyzer)
    fusion = ReciprocalRankFusion()
    engine = RetrievalEngine(planner, fusion)
    
    candidates = engine.retrieve("concept about attention", limit=5)
    assert len(candidates) == 2
    
    contents = [c.chunk.content for c in candidates]
    assert "metadata_result" in contents
    assert "dense_result" in contents

def test_context_builder() -> None:
    builder = DefaultContextBuilder()
    chunk = Chunk(id="c1", document_id="d1", content="Testing context")
    candidates = [Candidate(chunk=chunk, retrieval_score=1.0, retrieval_source="mock")]
    
    output = builder.build_context(candidates)
    assert "Testing context" in output
    assert "Source: mock" in output

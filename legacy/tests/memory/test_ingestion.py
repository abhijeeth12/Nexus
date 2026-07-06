"""Tests for Ingestion Subsystem."""

from typing import List, Any

from memory.models import Resource, Document, Chunk, IndexingStatus
from memory.interfaces.ingestion import IParser, IChunker, IEmbeddingProvider
from memory.interfaces.memory_service import IMemoryService
from core.models.tool_context import SafetyTier
from memory.ingestion.parser_registry import ParserRegistry
from memory.ingestion.pipeline import IngestionPipeline
from memory.ingestion.coordinator import IndexCoordinator

class MockParser(IParser):
    def parse(self, resource: Resource) -> Document:
        return Document(id=f"{resource.id}#doc", resource_id=resource.id, content="parsed content")

class MockChunker(IChunker):
    def chunk(self, document: Document) -> List[Chunk]:
        return [Chunk(id=f"{document.id}#c1", document_id=document.id, content="parsed chunk")]

class MockEmbedder(IEmbeddingProvider):
    def generate_embedding(self, text: str) -> List[float]: return [0.1]
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]: return [[0.1] for _ in texts]

class MockMemoryService(IMemoryService):
    def store_document(self, document: Document, chunks: List[Chunk]) -> bool: return True
    def store_resource_metadata(self, resource: Resource) -> bool: return True
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
    def get_recent_history(self, limit: int = 10) -> List[Any]: return []
    def store_interaction(self, session_id: str, role: str, content: str) -> bool: return True
    def store_session(self, session_id: str, title: str) -> bool: return True
    def store_transaction(self, tx: Any) -> bool: return True

def test_ingestion_pipeline() -> None:
    registry = ParserRegistry()
    registry.register("text/plain", MockParser())
    
    pipeline = IngestionPipeline(registry, MockChunker(), MockEmbedder(), MockMemoryService())
    resource = Resource(id="r1", resource_type="text/plain")
    
    assert pipeline.process(resource) is True

def test_index_coordinator() -> None:
    registry = ParserRegistry()
    registry.register("text/plain", MockParser())
    pipeline = IngestionPipeline(registry, MockChunker(), MockEmbedder(), MockMemoryService())
    
    coordinator = IndexCoordinator(pipeline)
    
    # First ingestion
    coordinator.handle_event("created", "r1", "text/plain", checksum="hash1")
    assert coordinator._resource_state["r1"].indexing_status == IndexingStatus.INDEXED
    assert coordinator._resource_state["r1"].metadata["version"] == 1
    
    # Incremental update (no change)
    coordinator.handle_event("modified", "r1", "text/plain", checksum="hash1")
    assert coordinator._resource_state["r1"].metadata["version"] == 1
    
    # Meaningful update
    coordinator.handle_event("modified", "r1", "text/plain", checksum="hash2")
    assert coordinator._resource_state["r1"].metadata["version"] == 2

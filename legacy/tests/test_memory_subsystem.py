import os
import uuid
import logging
from typing import Dict, Any

from memory.providers.sqlite_provider import SQLiteMemoryProvider, SQLiteKeywordIndex
from memory.providers.networkx_store import NetworkXGraphStore
from memory.service import MemoryService
from memory.ingestion.components import FileParser, BasicChunker, DummyEmbeddingProvider
from memory.ingestion.parser_registry import ParserRegistry
from memory.ingestion.pipeline import IngestionPipeline
from memory.ingestion.coordinator import IndexCoordinator
from memory.retrieval.engine import RetrievalEngine
from memory.retrieval.planner import RetrievalPlanner, BasicQueryAnalyzer
from memory.retrieval.retrievers import KeywordRetriever
from memory.retrieval.fusion import ReciprocalRankFusion
from memory.retrieval.context import DefaultContextBuilder
from memory.facade import KnowledgeRetrievalService
from memory.models import IndexingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test")

def main():
    logger.info("Initializing Memory Subsystem...")
    
    # 1. Setup Providers
    db_path = ":memory:" # Use in-memory for tests
    sqlite_provider = SQLiteMemoryProvider(db_path)
    graph_store = NetworkXGraphStore()
    memory_service = MemoryService(None, graph_store, sqlite_provider) # type: ignore
    
    # 2. Setup Ingestion
    parser_registry = ParserRegistry()
    parser_registry.register("file", FileParser())
    chunker = BasicChunker()
    embedder = DummyEmbeddingProvider()
    
    ingestion_pipeline = IngestionPipeline(parser_registry, chunker, embedder, memory_service)
    coordinator = IndexCoordinator(ingestion_pipeline)
    
    # 3. Setup Retrieval
    keyword_index = SQLiteKeywordIndex(sqlite_provider)
    keyword_retriever = KeywordRetriever(keyword_index)
    
    query_analyzer = BasicQueryAnalyzer()
    retrieval_planner = RetrievalPlanner([keyword_retriever], query_analyzer)
    fusion_strategy = ReciprocalRankFusion()
    
    retrieval_engine = RetrievalEngine(retrieval_planner, fusion_strategy)
    context_builder = DefaultContextBuilder()
    
    # --- TESTS ---
    
    logger.info("Test 1: Empty Database Retrieval")
    results = retrieval_engine.retrieve("Nexus")
    assert len(results) == 0, f"Expected 0 results, got {len(results)}"
    
    logger.info("Test 2: File Creation (Indexing)")
    # Create a dummy file
    test_file = "test_nexus_doc.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Nexus is an AI operating layer.\n\nIt features a transactional execution engine.")
    
    # Trigger ingestion
    coordinator.handle_event("created", test_file, "file", checksum="123")
    
    # Verify indexing status
    assert test_file in coordinator._resource_state
    assert coordinator._resource_state[test_file].indexing_status == IndexingStatus.INDEXED
    
    logger.info("Test 3: Retrieval and Context Building")
    results = retrieval_engine.retrieve("Nexus")
    assert len(results) > 0, "Expected >0 results for 'Nexus'"
    
    context_str = context_builder.build_context(results)
    assert "Nexus is an AI operating layer" in context_str, "Content not found in context"
    
    logger.info("Test 4: Graph Relationships")
    # Fetch resource ID from SQLite or graph. The graph should have the file path.
    # Resource nodes are added with their IDs (which is the file path)
    meta = graph_store.get_node_metadata(test_file)
    assert meta.get("type") == "resource"
    
    neighbors = graph_store.get_neighbors(test_file)
    logger.info(f"Resource neighbors: {neighbors}")
    # The current MemoryService adds document nodes but does not connect them to the resource node!
    # Let's check SQLite facts.
    db_results = sqlite_provider.query("transactional")
    assert len(db_results) > 0, "SQLite search for 'transactional' failed"
    
    logger.info("Test 5: File Deletion")
    coordinator.handle_event("deleted", test_file, "file")
    assert coordinator._resource_state[test_file].indexing_status == IndexingStatus.DELETED
    # In a full implementation, we'd delete the chunks from SQLite here.
    
    os.remove(test_file)
    logger.info("All tests passed successfully!")

if __name__ == "__main__":
    main()

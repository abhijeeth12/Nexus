"""Ingestion Pipeline."""

import logging
from memory.models import Resource
from memory.interfaces.ingestion import IChunker, IEmbeddingProvider
from memory.ingestion.parser_registry import ParserRegistry
from memory.interfaces.memory_service import IMemoryService

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Explicit, independent one-way ingestion pipeline."""
    
    def __init__(self, registry: ParserRegistry, chunker: IChunker, 
                 embedder: IEmbeddingProvider, memory_service: IMemoryService) -> None:
        self._registry = registry
        self._chunker = chunker
        self._embedder = embedder
        self._memory = memory_service
        
    def process(self, resource: Resource) -> bool:
        # Step 1: Parse
        try:
            parser = self._registry.get_parser(resource.resource_type)
            document = parser.parse(resource)
            # Store metadata regardless of embedding success/failure
            self._memory.store_resource_metadata(resource)
        except Exception as e:
            logger.error(f"Parsing failed for {resource.id}: {e}")
            return False
            
        # Step 2: Chunk
        try:
            chunks = self._chunker.chunk(document)
        except Exception as e:
            logger.error(f"Chunking failed for {document.id}: {e}")
            return False
            
        # Step 3: Embed
        embeddings_success = True
        try:
            texts = [c.content for c in chunks]
            if texts:
                embeddings = self._embedder.generate_embeddings(texts)
                for c, emb in zip(chunks, embeddings):
                    c.embedding = emb
        except Exception as e:
            logger.warning(f"Embedding failed for {document.id}: {e}")
            embeddings_success = False
            
        # Step 4: Store in MemoryService
        try:
            success = self._memory.store_document(document, chunks)
            return success and embeddings_success
        except Exception as e:
            logger.error(f"Storage failed for {document.id}: {e}")
            return False

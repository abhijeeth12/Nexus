"""Basic Ingestion Components."""

import os
from typing import List

from memory.interfaces.ingestion import IParser, IChunker, IEmbeddingProvider
from memory.models import Resource, Document, Chunk
import uuid

class FileParser(IParser):
    """Basic parser for text files."""
    def parse(self, resource: Resource) -> Document:
        file_path = resource.id
        content = ""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = f"File {file_path} (File not found)"
        except Exception as e:
            content = f"Error reading file {file_path}: {e}"
            
        return Document(
            id=str(uuid.uuid4()),
            resource_id=resource.id,
            content=content,
            metadata={"file_path": file_path, **resource.metadata}
        )

class BasicChunker(IChunker):
    """Splits a document into simple chunks based on size or paragraphs."""
    def chunk(self, document: Document) -> List[Chunk]:
        # Very simple naive chunker: split by double newline
        paragraphs = [p.strip() for p in document.content.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [document.content]
            
        chunks = []
        for i, p in enumerate(paragraphs):
            chunks.append(Chunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                content=p,
                metadata={"index": i, **document.metadata}
            ))
        return chunks

class DummyEmbeddingProvider(IEmbeddingProvider):
    """Dummy embedding provider that doesn't actually embed, to save memory/speed in local prototype."""
    def generate_embedding(self, text: str) -> List[float]:
        return []
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[] for _ in texts]

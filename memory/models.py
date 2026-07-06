"""Core memory models."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import uuid
from enum import Enum

class IndexingStatus(str, Enum):
    PENDING = "pending"
    INDEXED = "indexed"
    UPDATING = "updating"
    FAILED = "failed"
    DELETED = "deleted"

class Resource(BaseModel):
    """
    A generic operating system resource (File, Email, Repo, etc.).
    Uses a stable internal ID rather than path for identity.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checksum: Optional[str] = None
    indexing_status: IndexingStatus = IndexingStatus.PENDING

class Document(BaseModel):
    """An indexable textual representation parsed from a Resource."""
    id: str
    resource_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1

class Chunk(BaseModel):
    """The smallest retrievable semantic unit of a Document."""
    id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

class Candidate(BaseModel):
    """A retrieved candidate returned by a Retrieval Provider."""
    document: Optional[Document] = None
    chunk: Chunk
    retrieval_score: float
    retrieval_source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retrieval_evidence: Dict[str, Any] = Field(default_factory=dict)

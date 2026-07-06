"""Workflow Objects representing the immutable DataGraph (Provenance)."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid
import hashlib
import json

class WorkflowObject(BaseModel):
    """Base class for all persistent workflow artifacts (Strictly Immutable)."""
    model_config = ConfigDict(frozen=True)
    
    object_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    object_type: str = "WorkflowObject"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Provenance Tracking
    producer_capability: str
    producer_execution_id: str
    parent_object_ids: List[str] = Field(default_factory=list)
    
    # Metadata & Lifecycle
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0"
    
    @property
    def checksum(self) -> str:
        """Deterministic hash of the object content (excluding transient IDs/Timestamps)."""
        content_dict = self.model_dump(exclude={"object_id", "created_at", "producer_execution_id"})
        return hashlib.sha256(json.dumps(content_dict, sort_keys=True).encode()).hexdigest()

class DatasetObject(WorkflowObject):
    object_type: str = "DatasetObject"
    records: List[Dict[str, Any]] = Field(default_factory=list)
    schema_info: Dict[str, Any] = Field(default_factory=dict)

class DirectoryObject(WorkflowObject):
    object_type: str = "DirectoryObject"
    absolute_path: str
    file_count: int

class FileObject(WorkflowObject):
    object_type: str = "FileObject"
    absolute_path: str
    size_bytes: int
    content_hash: Optional[str] = None

class SummaryObject(WorkflowObject):
    object_type: str = "SummaryObject"
    content: str
    
class CodePatchObject(WorkflowObject):
    object_type: str = "CodePatchObject"
    target_file: str
    diff_content: str
    
class ExecutionReportObject(WorkflowObject):
    object_type: str = "ExecutionReportObject"
    status: str
    logs: List[str] = Field(default_factory=list)

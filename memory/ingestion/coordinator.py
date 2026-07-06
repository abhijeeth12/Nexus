"""Index Coordinator."""

import logging
from typing import Dict, Any, Optional
from memory.models import Resource, IndexingStatus
from memory.ingestion.pipeline import IngestionPipeline

logger = logging.getLogger(__name__)

class IndexCoordinator:
    """Coordinates filesystem events and manages indexing status & retries."""
    
    def __init__(self, pipeline: IngestionPipeline) -> None:
        self._pipeline = pipeline
        self._resource_state: Dict[str, Resource] = {}
        
    def handle_event(self, event_type: str, resource_id: str, resource_type: str, checksum: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        if event_type == "deleted":
            if resource_id in self._resource_state:
                self._resource_state[resource_id].indexing_status = IndexingStatus.DELETED
                # Future: Tell memory service to delete the document and chunks
            return
            
        # Incremental check
        if resource_id in self._resource_state:
            existing = self._resource_state[resource_id]
            if existing.checksum and existing.checksum == checksum:
                logger.debug(f"Skipping {resource_id}, checksum matches.")
                return
            existing.indexing_status = IndexingStatus.UPDATING
            existing.checksum = checksum
            version = existing.metadata.get("version", 1) + 1
            existing.metadata.update(metadata or {})
            existing.metadata["version"] = version
            resource = existing
        else:
            meta = metadata or {}
            meta["version"] = 1
            resource = Resource(id=resource_id, resource_type=resource_type, checksum=checksum, metadata=meta, indexing_status=IndexingStatus.PENDING)
            self._resource_state[resource_id] = resource
            
        self._dispatch(resource)
        
    def _dispatch(self, resource: Resource) -> None:
        max_retries = 3
        attempts = 0
        
        while attempts < max_retries:
            success = self._pipeline.process(resource)
            if success:
                resource.indexing_status = IndexingStatus.INDEXED
                return
            attempts += 1
            
        resource.indexing_status = IndexingStatus.FAILED
        logger.error(f"Failed to index {resource.id} after {max_retries} attempts.")

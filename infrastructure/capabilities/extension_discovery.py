"""Extension Discovery Capability Plugin."""

import os
from typing import Dict, Any, List
from core.interfaces.kernel import ICapabilityPlugin
from core.models.contracts import CapabilityContract
from core.models.workflow_objects import DatasetObject
from memory.storage.extension_tree import ExtensionIndexTree

_SHARED_EXTENSION_TREE = ExtensionIndexTree()

class ExtensionDiscoveryPlugin(ICapabilityPlugin):
    
    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            capability_name="extension_search",
            description="Discovers files or repositories matching an extension, yielding a structured DatasetObject.",
            accepted_input_types=["extension", "search_root"],
            produced_output_types=["DatasetObject"],
            cacheable=True,
            deterministic=False
        )
        
    def execute(self, context: Any, inputs: Dict[str, Any]) -> List[Any]:
        extension = inputs.get("extension", "")
        search_root = inputs.get("search_root") or context.workspace
        
        if not _SHARED_EXTENSION_TREE.root.children:
            for root, dirs, files in os.walk(search_root):
                for d in dirs:
                    if d == ".git":
                        _SHARED_EXTENSION_TREE.add_path(os.path.join(root, d))
                for f in files:
                    _SHARED_EXTENSION_TREE.add_path(os.path.join(root, f))
                    
        results = _SHARED_EXTENSION_TREE.search(extension, search_root)
        
        records = []
        for path, doc_id in results:
            records.append({
                "document_id": doc_id,
                "path": path,
                "size_bytes": os.path.getsize(path) if os.path.exists(path) else 0
            })
            
        dataset = DatasetObject(
            producer_capability="extension_search",
            producer_execution_id="PENDING",
            parent_object_ids=[],
            records=records
        )
        
        return [dataset]

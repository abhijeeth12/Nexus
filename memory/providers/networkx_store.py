"""NetworkX Graph Store."""

import networkx as nx # type: ignore
from typing import List, Dict, Any

from memory.interfaces.storage import IGraphStore

class NetworkXGraphStore(IGraphStore):
    """Concrete implementation of IGraphStore using NetworkX."""
    
    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        
    def add_node(self, node_id: str, metadata: Dict[str, Any]) -> None:
        self._graph.add_node(node_id, **metadata)
        
    def add_edge(self, source_id: str, target_id: str, relationship: str) -> None:
        self._graph.add_edge(source_id, target_id, relationship=relationship)
        
    def get_neighbors(self, node_id: str) -> List[str]:
        if node_id in self._graph:
            return list(self._graph.successors(node_id)) + list(self._graph.predecessors(node_id))
        return []
        
    def get_node_metadata(self, node_id: str) -> Dict[str, Any]:
        if node_id in self._graph:
            return dict(self._graph.nodes[node_id])
        return {}

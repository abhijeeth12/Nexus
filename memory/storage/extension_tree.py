"""In-memory Extension Index Tree (Low-Level Service)."""

import os
from typing import Dict, List, Tuple, Optional, Generator
import uuid
import json

class TreeNode:
    def __init__(self, name: str, is_leaf: bool = False, document_id: Optional[str] = None):
        self.name = name
        self.is_leaf = is_leaf
        self.document_id = document_id
        self.children: Dict[str, 'TreeNode'] = {}
        
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "is_leaf": self.is_leaf,
            "document_id": self.document_id,
            "children": {k: v.to_dict() for k, v in self.children.items()}
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'TreeNode':
        node = cls(name=data["name"], is_leaf=data["is_leaf"], document_id=data.get("document_id"))
        for k, v in data.get("children", {}).items():
            node.children[k] = cls.from_dict(v)
        return node

class ExtensionIndexTree:
    """
    Maintains an in-memory index mapping File Extensions -> Absolute Path Hierarchy.
    Provides fast, scoped DFS search without traversing the actual filesystem.
    """
    
    def __init__(self) -> None:
        # The root holds extensions as keys, e.g., ".py", ".md", ".git"
        self.root = TreeNode("ROOT")
        # O(1) global count of files per extension
        self.extension_counts: Dict[str, int] = {}
        
    def _normalize_path_parts(self, path: str) -> List[str]:
        path = os.path.normpath(path)
        parts = []
        while True:
            path, folder = os.path.split(path)
            if folder:
                parts.append(folder)
            elif path:
                parts.append(path)
                break
        parts.reverse()
        return parts

    def add_path(self, absolute_path: str, document_id: Optional[str] = None) -> None:
        if not document_id:
            document_id = str(uuid.uuid4())
            
        filename = os.path.basename(absolute_path)
        if absolute_path.endswith(".git") or filename == ".git":
            ext = ".git"
        else:
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            if not ext:
                ext = ".no_ext"
                
        if ext not in self.root.children:
            self.root.children[ext] = TreeNode(ext)
            
        ext_node = self.root.children[ext]
        
        parts = self._normalize_path_parts(absolute_path)
        current = ext_node
        
        for i, part in enumerate(parts):
            if part not in current.children:
                is_leaf = (i == len(parts) - 1)
                current.children[part] = TreeNode(part, is_leaf=is_leaf, document_id=document_id if is_leaf else None)
                if is_leaf:
                    # Increment O(1) counter when a new leaf is added
                    self.extension_counts[ext] = self.extension_counts.get(ext, 0) + 1
            current = current.children[part]
            
    def _dfs_search(self, node: TreeNode, current_path_buffer: List[str], search_root_parts: Optional[List[str]]) -> Generator[Tuple[str, str], None, None]:
        depth = len(current_path_buffer)
        
        # Enforce search scope prune
        if search_root_parts and depth <= len(search_root_parts):
            # Check if the path so far matches the search root
            # Convert both to lowercase for Windows path matching safety
            if current_path_buffer[depth-1].lower() != search_root_parts[depth-1].lower():
                return
                
        if node.is_leaf and node.document_id:
            # Reconstruct absolute path from buffer
            yield (os.path.join(*current_path_buffer), node.document_id)
            return
            
        for child_name, child_node in node.children.items():
            current_path_buffer.append(child_name)
            yield from self._dfs_search(child_node, current_path_buffer, search_root_parts)
            current_path_buffer.pop()

    def search(self, extension: str, search_root: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Returns a list of (absolute_path, document_id) for the given extension.
        Optionally scoped under search_root using DFS.
        """
        ext = extension.lower()
        if ext not in self.root.children:
            return []
            
        search_parts = None
        if search_root:
            search_parts = self._normalize_path_parts(search_root)
            
        results = []
        ext_node = self.root.children[ext]
        for child_name, child_node in ext_node.children.items():
            buffer = [child_name]
            for res in self._dfs_search(child_node, buffer, search_parts):
                results.append(res)
                
        return results

    def save_to_disk(self, cache_path: str) -> None:
        """Serializes the entire tree and counts to a JSON cache file."""
        data = {
            "extension_counts": self.extension_counts,
            "root": self.root.to_dict()
        }
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
    def load_from_disk(self, cache_path: str) -> bool:
        """Loads the tree from a JSON cache file if it exists. Returns True if successful."""
        if not os.path.exists(cache_path):
            return False
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.extension_counts = data.get("extension_counts", {})
            self.root = TreeNode.from_dict(data.get("root", {}))
            return True
        except Exception:
            return False

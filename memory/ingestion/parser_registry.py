"""Parser Registry."""

from typing import Dict
from memory.interfaces.ingestion import IParser

class ParserRegistry:
    """Selects the correct parser based on resource type."""
    def __init__(self) -> None:
        self._parsers: Dict[str, IParser] = {}
        
    def register(self, resource_type: str, parser: IParser) -> None:
        self._parsers[resource_type] = parser
        
    def get_parser(self, resource_type: str) -> IParser:
        if resource_type not in self._parsers:
            raise ValueError(f"No parser registered for resource type: {resource_type}")
        return self._parsers[resource_type]

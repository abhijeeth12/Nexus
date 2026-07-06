"""Retrieval interfaces."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from memory.models import Candidate

class IRetriever(ABC):
    """Modular retrieval strategy interface."""
    @property
    @abstractmethod
    def name(self) -> str: pass
    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> List[Candidate]: pass

class IRankFusionStrategy(ABC):
    """Strategy for fusing multiple candidate lists."""
    @abstractmethod
    def fuse(self, candidate_lists: List[List[Candidate]], limit: int) -> List[Candidate]: pass

class IContextBuilder(ABC):
    """Expands context (e.g., sibling/parent blocks) and formats final output."""
    @abstractmethod
    def build_context(self, candidates: List[Candidate]) -> str: pass

class IQueryAnalyzer(ABC):
    """Analyzes natural language to determine which retrieval strategies to apply."""
    @abstractmethod
    def analyze(self, query: str) -> Dict[str, Any]: pass

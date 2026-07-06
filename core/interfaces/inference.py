"""Inference abstractions."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class RateLimitError(Exception):
    """Raised when an inference engine hits a rate limit."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class ModelMetadata(BaseModel):
    """Metadata about an installed inference model."""
    id: str
    name: str
    parameter_size: str
    quantization: str
    is_local: bool

class InferenceRequest(BaseModel):
    """A structured request to an inference engine."""
    system_prompt: str
    user_prompt: str
    schema_format: Optional[Dict[str, Any]] = None
    temperature: float = 0.0
    model_override: Optional[str] = None

class InferenceResponse(BaseModel):
    """A standard response from an inference engine."""
    content: str
    finish_reason: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw_response: Any = Field(default=None, exclude=True)

class IInferenceEngine(ABC):
    """The absolute gateway for all LLM inference in the system."""
    
    @abstractmethod
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Generates a completion based on the request."""
        pass

class IModelManager(ABC):
    """Manages models, versions, and downloads for the inference engine."""
    
    @abstractmethod
    def list_installed_models(self) -> List[ModelMetadata]:
        pass
        
    @abstractmethod
    def download_model(self, model_name: str) -> bool:
        pass
        
    @abstractmethod
    def get_default_model(self) -> str:
        pass

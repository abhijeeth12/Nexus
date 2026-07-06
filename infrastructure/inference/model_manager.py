"""Ollama Model Manager."""

import ollama
import logging
from typing import List

from core.interfaces.inference import IModelManager, ModelMetadata

logger = logging.getLogger(__name__)

class OllamaModelManager(IModelManager):
    """Concrete implementation of IModelManager using Ollama."""
    
    def __init__(self, default_model: str = "llama3.2") -> None:
        self._default_model = default_model
        
    def list_installed_models(self) -> List[ModelMetadata]:
        try:
            models_response = ollama.list()
            metadata_list = []
            for m in models_response.get("models", []):
                details = m.get("details", {})
                metadata_list.append(ModelMetadata(
                    id=m.get("digest", ""),
                    name=m.get("model", ""),
                    parameter_size=details.get("parameter_size", "unknown"),
                    quantization=details.get("quantization_level", "unknown"),
                    is_local=True
                ))
            return metadata_list
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
            
    def download_model(self, model_name: str) -> bool:
        try:
            logger.info(f"Downloading model {model_name}...")
            ollama.pull(model_name)
            return True
        except Exception as e:
            logger.error(f"Failed to download model {model_name}: {e}")
            return False
            
    def get_default_model(self) -> str:
        return self._default_model

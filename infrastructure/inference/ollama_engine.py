"""Ollama Inference Engine."""

import json
import logging
from typing import Optional
import ollama

from core.interfaces.inference import IInferenceEngine, InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)

class OllamaInferenceEngine(IInferenceEngine):
    """Concrete implementation of IInferenceEngine using local Ollama."""
    
    def __init__(self, default_model: str = "qwen2.5:7B") -> None:
        self._default_model = default_model
        self._client = ollama.Client(host='http://127.0.0.1:11434')
        
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        model = request.model_override or self._default_model
        
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt}
        ]
        
        # Ollama supports passing Pydantic schema dict via 'format' in later versions,
        # but smaller models or complex schemas cause the llama.cpp runner to terminate.
        # We fallback to format="json" and prompt engineering to ensure stability.
        try:
            response = self._client.chat(
                model=model,
                messages=messages,
                options={"temperature": request.temperature, "num_ctx": 8192, "think": False}
            )
            
            return InferenceResponse(
                content=response.get("message", {}).get("content") or "",
                finish_reason=response.get("done_reason") or "stop",
                prompt_tokens=response.get("prompt_eval_count") or 0,
                completion_tokens=response.get("eval_count") or 0,
                raw_response=response
            )
        except Exception as e:
            logger.error(f"Ollama inference failed: {e}")
            raise RuntimeError(f"Ollama inference failed: {e}")

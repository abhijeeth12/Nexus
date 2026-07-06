"""Gemini Inference Engine."""

import os
import logging
from typing import Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import TooManyRequests

from core.interfaces.inference import IInferenceEngine, InferenceRequest, InferenceResponse, RateLimitError

logger = logging.getLogger(__name__)

class GeminiInferenceEngine(IInferenceEngine):
    """Concrete implementation of IInferenceEngine using Google's Gemini."""
    
    def __init__(self, api_key: str, default_model: str = "gemini-2.5-flash") -> None:
        self._default_model = default_model
        genai.configure(api_key=api_key)
        
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        model_name = request.model_override or self._default_model
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=request.system_prompt
        )
        
        # We enforce JSON if schema_format or strict json is requested
        response_mime_type = "application/json"
        
        try:
            response = model.generate_content(
                request.user_prompt,
                generation_config=GenerationConfig(
                    temperature=request.temperature,
                    response_mime_type=response_mime_type,
                )
            )
            
            return InferenceResponse(
                content=response.text,
                finish_reason="stop" if response.candidates[0].finish_reason == 1 else "unknown",
                prompt_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                completion_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                raw_response={"text": response.text}
            )
        except TooManyRequests as e:
            logger.warning(f"Gemini API rate limit exceeded: {e}")
            raise RateLimitError("Gemini API rate limit exceeded", retry_after=60)
        except Exception as e:
            logger.error(f"Gemini inference failed: {e}")
            raise RuntimeError(f"Gemini inference failed: {e}")

"""Provider Manager for intelligent fallback and rate limiting."""

import time
import logging
from typing import List, Dict

from core.interfaces.inference import IInferenceEngine, InferenceRequest, InferenceResponse, RateLimitError

logger = logging.getLogger(__name__)

class ProviderManager(IInferenceEngine):
    """Manages multiple inference engines with automatic fallback and rate limit handling."""
    
    def __init__(self, providers: List[IInferenceEngine]):
        if not providers:
            raise ValueError("At least one provider must be configured.")
        self.providers = providers
        # Map of provider id() to the epoch time when they are available again
        self._cooldowns: Dict[int, float] = {}

    def _is_available(self, provider: IInferenceEngine) -> bool:
        pid = id(provider)
        if pid in self._cooldowns:
            if time.time() < self._cooldowns[pid]:
                return False
            else:
                del self._cooldowns[pid]
        return True

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        last_error = None
        
        for provider in self.providers:
            if not self._is_available(provider):
                continue
                
            try:
                # logger.debug(f"Attempting inference with {provider.__class__.__name__}")
                return provider.generate(request)
            except RateLimitError as e:
                logger.warning(f"Rate limit hit on {provider.__class__.__name__}. Cooling down for {e.retry_after}s. Error: {e}")
                self._cooldowns[id(provider)] = time.time() + e.retry_after
                last_error = e
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                last_error = e
                
        # If we reach here, all available providers failed or are on cooldown
        raise RuntimeError(f"All inference providers failed or are rate limited. Last error: {last_error}")

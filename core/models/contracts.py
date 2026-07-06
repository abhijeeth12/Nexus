"""Capability Contracts."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class CapabilityContract(BaseModel):
    """Formal schema defining a capability's inputs, outputs, and constraints."""
    capability_name: str
    version: str = "1.0"
    description: str
    accepted_input_types: List[str] = Field(default_factory=list)
    produced_output_types: List[str] = Field(default_factory=list)
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="Full JSON Schema for the capability's input parameters.")
    required_permissions: List[str] = Field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_runtime_ms: int = 1000
    cacheable: bool = False
    deterministic: bool = False
    side_effects: bool = False
    parallel_safe: bool = True
    rollback_supported: bool = False

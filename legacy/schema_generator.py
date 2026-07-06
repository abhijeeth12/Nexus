"""Schema generator for the Planner."""

from typing import Any, Dict
from agents.registry import CapabilityRegistry

class SchemaGenerator:
    """Converts the Capability Registry into a dynamic JSON Schema for the LLM."""
    
    @staticmethod
    def generate_registry_schema(registry: CapabilityRegistry) -> Dict[str, Any]:
        """Generates a schema mapping agents to their available tools and parameter schemas."""
        schema: Dict[str, Any] = {}
        for agent_name, tools in registry.get_all_capabilities().items():
            agent_schema: Dict[str, Any] = {}
            for tool in tools:
                tool_schema = tool.input_schema.model_json_schema()
                agent_schema[tool.name] = {
                    "description": tool.description,
                    "parameters": tool_schema.get("properties", {}),
                    "defs": tool_schema.get("$defs", {})
                }
            schema[agent_name] = agent_schema
        return schema

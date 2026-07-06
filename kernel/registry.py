"""Capability Registry for loading plugins."""
from core.interfaces.kernel import ICapabilityRegistry, ICapabilityPlugin
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class CapabilityRegistry(ICapabilityRegistry):
    """Manages loaded plugins and their contracts."""
    
    def __init__(self) -> None:
        self._plugins: Dict[str, ICapabilityPlugin] = {}
        
    def register_plugin(self, plugin: ICapabilityPlugin) -> None:
        contract = plugin.get_contract()
        self._plugins[contract.capability_name] = plugin
        logger.info(f"Registered capability plugin: {contract.capability_name}")
        
    def get_contract(self, capability_name: str) -> Optional[Any]:
        plugin = self._plugins.get(capability_name)
        if plugin:
            return plugin.get_contract()
        return None
        
    def get_plugin(self, capability_name: str) -> Optional[ICapabilityPlugin]:
        return self._plugins.get(capability_name)
        
    def load_plugins(self, path: str) -> None:
        # Static registration for now in V2 bootstrap
        pass
        
    def dump_schemas(self) -> list:
        return [p.get_contract().model_dump(mode='json') for p in self._plugins.values()]

class LegacyToolAdapter(ICapabilityPlugin):
    """Adapts a legacy V1 BaseTool into a V2 CapabilityPlugin."""
    
    def __init__(self, tool_instance: Any):
        self.tool = tool_instance
        
    def get_contract(self) -> 'CapabilityContract':
        from core.models.contracts import CapabilityContract
        # Generate full JSON schema from the tool's Pydantic input model
        full_schema = self.tool.input_schema.model_json_schema()
        parameters_schema = {
            "properties": full_schema.get("properties", {}),
            "required": full_schema.get("required", []),
        }
        return CapabilityContract(
            capability_name=self.tool.name,
            description=self.tool.description,
            accepted_input_types=list(self.tool.input_schema.model_fields.keys()),
            produced_output_types=["SummaryObject"],
            parameters_schema=parameters_schema,
            cacheable=False,
            deterministic=False
        )
        
    def execute(self, context: Any, inputs: Dict[str, Any]) -> list:
        from core.models.tool_context import ToolContext
        from core.models.workflow_objects import SummaryObject
        import uuid
        
        legacy_context = ToolContext(
            transaction_id=str(uuid.uuid4()),
            working_directory=context.workspace
        )
        
        result = self.tool.execute(legacy_context, **inputs)
        
        if not result.success:
            raise RuntimeError(f"Tool {self.tool.name} failed: {result.error}")
            
        summary = SummaryObject(
            producer_capability=self.tool.name,
            producer_execution_id="PENDING",
            parent_object_ids=[],
            content=str(result.output)
        )
        return [summary]


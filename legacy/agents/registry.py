"""Capability Registry."""

from typing import Dict, List, Optional
from core.interfaces.agent import IAgent
from core.interfaces.tool import ITool

class CapabilityRegistry:
    """Dynamically tracks available agents and their capabilities."""
    
    def __init__(self) -> None:
        self._agents: Dict[str, IAgent] = {}
        
    def register_agent(self, agent: IAgent) -> None:
        """Registers a new agent into the system."""
        self._agents[agent.name] = agent
        
    def get_agent(self, name: str) -> Optional[IAgent]:
        """Retrieves an agent by its name."""
        return self._agents.get(name)
        
    def get_all_capabilities(self) -> Dict[str, List[ITool]]:
        """
        Returns a map of all agents and their provided tools.
        The Planner will use this schema to generate valid instructions.
        """
        return {name: agent.get_capabilities() for name, agent in self._agents.items()}
        
    def has_capability(self, agent_name: str, intent_name: str) -> bool:
        """Checks if a specific intent is supported by an agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            return False
        return any(tool.name == intent_name for tool in agent.get_capabilities())

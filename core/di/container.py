"""Dependency Injection Container."""

from dependency_injector import containers, providers

from core.interfaces.engine import IExecutionEngine
from core.interfaces.memory import IMemoryProvider

class NexusContainer(containers.DeclarativeContainer):
    """
    Central Dependency Injection Container for Nexus.
    
    Providers defined as Dependencies act as placeholders 
    for abstract interfaces. They must be overridden with 
    concrete implementations at runtime or during testing.
    """
    
    # We use abstract interfaces here to enforce contracts.
    # The actual singletons will be wired during application startup.
    execution_engine = providers.Dependency(instance_of=IExecutionEngine) # type: ignore[type-abstract]
    memory_provider = providers.Dependency(instance_of=IMemoryProvider) # type: ignore[type-abstract]

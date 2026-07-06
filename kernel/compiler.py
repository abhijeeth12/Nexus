"""Workflow Compiler: Translates semantic graph into executable TaskGraph."""

from core.models.graph import TaskGraph, TaskNode, TaskState
from core.interfaces.kernel import ICapabilityRegistry
from typing import Dict, Any, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

class WorkflowCompiler:
    def __init__(self, registry: ICapabilityRegistry) -> None:
        self.registry = registry
        
    def compile(self, semantic_tasks: List[Dict[str, Any]], workflow_id: Optional[str] = None) -> TaskGraph:
        """
        Compiles a list of semantic tasks from the Planner into an executable TaskGraph.
        Validates contracts and resolves capability names.
        """
        if not workflow_id:
            workflow_id = str(uuid.uuid4())
            
        graph = TaskGraph(workflow_id=workflow_id)
        
        for t in semantic_tasks:
            cap_name = t.get("capability_name")
            if not cap_name:
                logger.warning(f"Task {t.get('task_id')} missing capability_name. Skipping.")
                continue
                
            contract = self.registry.get_contract(cap_name)
            if not contract:
                logger.warning(f"Capability '{cap_name}' not found in registry. Task {t.get('task_id')} dropped.")
                continue
                
            node = TaskNode(
                task_id=t.get("task_id", str(uuid.uuid4())),
                capability_name=cap_name,
                inputs=t.get("inputs", {}),
                dependencies=t.get("dependencies", []),
                priority=t.get("priority", 1),
                state=TaskState.CREATED
            )
            graph.nodes[node.task_id] = node
            
        return graph

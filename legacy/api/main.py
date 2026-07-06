"""FastAPI Main Router."""

from fastapi import FastAPI, Depends
from typing import Dict, Any
import uuid

from api.models import PlanRequest, ExecuteRequest
from api.dependencies import get_registry, get_orchestrator, get_planner
from agents.registry import CapabilityRegistry
from agents.orchestrator import Orchestrator
from planner.dummy_planner import DummyPlanner
from core.models.tool_context import ToolContext
from planner.schema_generator import SchemaGenerator

app = FastAPI(title="Nexus API")

@app.get("/capabilities")
def get_capabilities(registry: CapabilityRegistry = Depends(get_registry)) -> Dict[str, Any]:
    """Returns the JSON schema of all registered capabilities."""
    return SchemaGenerator.generate_registry_schema(registry)

@app.post("/plan")
def create_plan(
    request: PlanRequest, 
    planner: DummyPlanner = Depends(get_planner), 
    registry: CapabilityRegistry = Depends(get_registry)
) -> Any:
    """Generates a deterministic instruction plan from natural language."""
    return planner.plan(request.user_request, registry)

@app.post("/execute")
def execute_instruction(
    request: ExecuteRequest, 
    orchestrator: Orchestrator = Depends(get_orchestrator)
) -> Any:
    """Executes a strictly formatted instruction via the Orchestrator."""
    tx_id = str(uuid.uuid4())
    ctx = ToolContext(transaction_id=tx_id, working_directory=".")
    
    results = orchestrator.execute_instruction(request.agent_name, request.instruction, ctx)
    return {
        "transaction_id": tx_id, 
        "results": [r.model_dump() for r in results]
    }

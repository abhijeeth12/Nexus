"""Headless CLI Tester for End-to-End verification."""

import uuid
import json
from api.dependencies import get_registry, get_orchestrator, get_planner
from core.models.tool_context import ToolContext
from pathlib import Path

def run_headless() -> None:
    print("=== Initializing Nexus Headless Mode ===")
    registry = get_registry()
    planner = get_planner()
    orchestrator = get_orchestrator()
    
    # Create a dummy file to interact with
    dummy_file = Path("dummy.txt")
    dummy_file.write_text("Hello Nexus!")
    
    # 1. Natural Language Input
    request = "Please move dummy.txt to dummy_moved.txt"
    print(f"\n[USER] {request}")
    
    # 2. Planner
    plan = planner.plan(request, registry)
    print(f"\n[PLANNER] Goal: {plan.goal}")
    print(f"[PLANNER] Plan:\n{plan.model_dump_json(indent=2)}")
    
    if not plan.ordered_instructions:
        print("No instructions to execute.")
        return
        
    # 3. Execution
    for instr in plan.ordered_instructions:
        tx_id = str(uuid.uuid4())
        ctx = ToolContext(transaction_id=tx_id, working_directory=".")
        print(f"\n[ORCHESTRATOR] Submitting instruction '{instr.intent}' to '{instr.agent_name}'")
        
        # Override dummy parameters for real ones since dummy planner uses hardcoded params
        raw_instr = {
            "intent": instr.intent, 
            "parameters": {"source": "dummy.txt", "destination": "dummy_moved.txt"}
        }
        
        results = orchestrator.execute_instruction(instr.agent_name, raw_instr, ctx)
        for r in results:
            print(f"[ENGINE] Result -> Success: {r.success}, Output: {r.output}, Error: {r.error}")

if __name__ == "__main__":
    run_headless()

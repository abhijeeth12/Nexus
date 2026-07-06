"""Plan Validator."""

from typing import List, Dict, Any
import json

from core.models.instruction import ExecutionPlan
from agents.registry import CapabilityRegistry
from core.telemetry.logger import get_logger

logger = get_logger(__name__)

class PlanValidator:
    """Validates ExecutionPlans deterministically before execution."""
    
    def __init__(self, registry: CapabilityRegistry):
        self._registry = registry
        
    def validate(self, plan: ExecutionPlan, user_request: str) -> List[Dict[str, Any]]:
        """Returns a list of structured validation errors. Empty list means valid."""
        errors: List[Dict[str, Any]] = []
        
        if not plan.ordered_instructions:
            errors.append({
                "step_index": -1,
                "error": "empty_plan",
                "reason": "Plan contains no instructions.",
                "suggested_fix": "Generate valid instructions mapping to capabilities."
            })
            return errors
            
        req_lower = user_request.lower()
        is_global_request = any(word in req_lower for word in ["all", "entire", "everywhere", "system", "laptop", "pc", "computer", "every drive"])
        is_user_files_request = "my documents" in req_lower or "my files" in req_lower or "downloads" in req_lower
        
        for idx, instr in enumerate(plan.ordered_instructions):
            # Registry validation
            agent = self._registry.get_agent(instr.agent_name)
            if not agent:
                errors.append({
                    "step_index": idx,
                    "error": "unregistered_agent",
                    "reason": f"Agent '{instr.agent_name}' is not registered.",
                    "suggested_fix": "Select an agent from the provided capabilities registry."
                })
                continue
                
            tool_match = [t for t in agent.get_capabilities() if t.name == instr.intent]
            if not tool_match:
                errors.append({
                    "step_index": idx,
                    "error": "unregistered_intent",
                    "reason": f"Intent '{instr.intent}' not found on agent '{instr.agent_name}'.",
                    "suggested_fix": "Select a valid intent from the agent's capabilities."
                })
                continue
                
            tool = tool_match[0]
            
            # Schema validation
            if not tool.validate(**instr.parameters):
                errors.append({
                    "step_index": idx,
                    "error": "schema_mismatch",
                    "reason": f"Parameters {json.dumps(instr.parameters)} do not match schema for '{instr.intent}'.",
                    "suggested_fix": "Review the schema and provide valid parameters."
                })
                
            # Unresolved Parameter Validation
            has_placeholder = False
            for k, v in instr.parameters.items():
                if isinstance(v, str) and (v == "" or (v.startswith("{") and v.endswith("}"))):
                    if k in ["file_path", "path", "source", "destination", "query", "command"]:
                        errors.append({
                            "step_index": idx,
                            "error": "unresolved_parameter",
                            "reason": f"Parameter '{k}' is empty or contains a placeholder ({v}).",
                            "suggested_fix": "You cannot include steps in your plan if you do not know the required parameters yet. If a step depends on information discovered in a previous step (like a search), DO NOT include it in the current plan. Stop the plan early and only output the discovery steps."
                        })
                        has_placeholder = True
                        break
            if has_placeholder:
                continue
                
            # Scope Narrowing Validation
            if "scope" in instr.parameters:
                scope_val = instr.parameters["scope"]
                # If they asked for global, but the scope is something restricted like CURRENT_WORKSPACE or an explicit narrow path
                if is_global_request and scope_val not in ["ALL_DRIVES", "AUTO"]:
                    errors.append({
                        "step_index": idx,
                        "error": "scope_narrowing",
                        "expected_scope": "ALL_DRIVES or AUTO",
                        "actual_scope": scope_val,
                        "reason": "Planner reduced requested search scope.",
                        "suggested_fix": "Your plan narrowed the user's requested search scope without justification. Preserve the requested scope and choose the most appropriate capability. Do not assume specific drives or directories unless explicitly requested."
                    })
                # If they used an explicit path that looks like a drive root when they should have used a semantic scope
                elif scope_val == "EXPLICIT_PATH":
                    explicit_path = str(instr.parameters.get("explicit_path", "")).lower()
                    if explicit_path in ["c:\\", "c:", "d:\\", "d:"] and not (explicit_path in req_lower):
                        errors.append({
                            "step_index": idx,
                            "error": "unsupported_assumption",
                            "expected_scope": "Semantic Scope",
                            "actual_scope": explicit_path,
                            "reason": "Planner assumed a specific drive letter without justification.",
                            "suggested_fix": "Use semantic scopes (e.g., ALL_DRIVES, AUTO) instead of guessing concrete drive letters."
                        })
                        
            # Prevent arbitrary run_command root scans
            if instr.intent == "run_command":
                cmd = str(instr.parameters.get("command", "")).lower()
                if "get-childitem c:\\" in cmd or "find c:\\" in cmd or "get-childitem /" in cmd or "find /" in cmd:
                    errors.append({
                        "step_index": idx,
                        "error": "inappropriate_tool",
                        "reason": "Plan attempts to recursively search system roots via run_command.",
                        "suggested_fix": "Use structured intents like search_directory instead of open-ended terminal commands for recursive searches."
                    })
                            
        return errors

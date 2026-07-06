"""Plan Quality Scorer."""

from typing import Dict, Any

from core.models.instruction import ExecutionPlan

class PlanQualityScorer:
    """Scores execution plans heuristically for offline evaluation."""
    
    @staticmethod
    def score(plan: ExecutionPlan) -> Dict[str, float]:
        """Returns normalized scores (0.0 to 1.0) for various metrics."""
        scores = {
            "complexity": 1.0,
            "safety": 1.0,
            "structured_usage": 0.0,
            "abstraction_quality": 1.0
        }
        
        if not plan.ordered_instructions:
            return scores
            
        # Complexity penalty for too many steps
        num_steps = len(plan.ordered_instructions)
        if num_steps > 5:
            scores["complexity"] -= (num_steps - 5) * 0.1
            
        # Structure usage (reward using structured operations over raw run_command)
        structured_count = sum(1 for i in plan.ordered_instructions if i.intent != "run_command")
        scores["structured_usage"] = structured_count / num_steps if num_steps > 0 else 0.0
        
        # Safety penalty for raw commands
        raw_cmd_count = num_steps - structured_count
        if raw_cmd_count > 0:
            scores["safety"] -= raw_cmd_count * 0.15
            
        # Abstraction and assumption penalties
        for instr in plan.ordered_instructions:
            # Unnecessary browser usage heuristic
            if instr.agent_name == "browser_agent":
                scores["complexity"] -= 0.1
            
            # Implementation details leaking
            for k, v in instr.parameters.items():
                if isinstance(v, str):
                    v_lower = v.lower()
                    if v_lower.startswith("c:\\") or v_lower.startswith("d:\\") or "/home" in v_lower:
                        scores["abstraction_quality"] -= 0.2
        
        # Penalize if plan failed validation and couldn't be fully corrected
        if "validation_errors" in plan.metadata:
            errors = plan.metadata["validation_errors"]
            for err in errors:
                err_type = err.get("error", "")
                if err_type == "scope_narrowing":
                    scores["abstraction_quality"] -= 0.4
                elif err_type == "unsupported_assumption":
                    scores["abstraction_quality"] -= 0.3
                elif err_type == "inappropriate_tool":
                    scores["safety"] -= 0.3
                    scores["abstraction_quality"] -= 0.3
                else:
                    scores["safety"] -= 0.1
            
        # Ensure bounds
        for k, v in scores.items():
            scores[k] = max(0.0, min(1.0, v))
            
        return scores

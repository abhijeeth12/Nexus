"""Live Planner using Inference Engine (V2)."""

import os
import json
import logging
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from core.interfaces.planner import IPlanner
from core.interfaces.inference import IInferenceEngine, InferenceRequest
from core.interfaces.kernel import ICapabilityRegistry
from core.models.instruction import GraphUpdate

logger = logging.getLogger(__name__)

class PlannerContext(BaseModel):
    goal: str
    turn_count: int
    task_graph: Dict[str, Any]
    data_graph_summaries: List[Dict[str, Any]]
    working_memory: Dict[str, Any]
    output_document: str = ""
    perceived_insights: str = ""
    failed_tasks: List[Dict[str, Any]] = Field(default_factory=list)

class LivePlanner(IPlanner):
    """A real LLM planner that generates deterministic execution plans."""
    
    def __init__(self, inference_engine: IInferenceEngine) -> None:
        self._engine = inference_engine
        

        
    def _clean_json(self, content: str) -> str:
        import re
        content = content.strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return match.group(0)
        return content
        
    def plan(self, context: PlannerContext, registry: ICapabilityRegistry) -> GraphUpdate:
        registry_schema = registry.dump_schemas()
        
        system_prompt = f"""You are Nexus V2, an advanced Stateful Iterative Workflow Operating System.
You operate as the Kernel Planner. You do not execute low-level commands directly.
Instead, you orchestrate high-level 'Capability Contracts' by building a Task Graph.

ARCHITECTURE CONTEXT:
You operate in a direct data pipeline:
1. Tool Execution: The tools you schedule are executed and their raw JSON outputs are provided back to you as 'Raw Tool Outputs'.
2. Planning (You): You parse the Raw Tool Outputs, extract the exact data you need, and meticulously save it into your 'Working Memory'. You then append to the 'Output Document' (which the user sees), and schedule the next 'new_tasks'.

Available Capabilities:
{json.dumps(registry_schema, indent=2)}

CRITICAL RULES FOR CAPABILITIES:
1. DO NOT HALLUCINATE OR INVENT CAPABILITIES.
2. You MUST ONLY use the capability names exactly as they are listed in the 'Available Capabilities' JSON above.
3. If you try to schedule a capability (like 'magic_do_everything_tool') that is NOT in the JSON array above, the system will CRASH. Use ONLY the exact strings provided in 'capability_name'.
4. SMART DISCOVERY WORKFLOW: You MUST run `list_dir` on `/` or `C:\\` FIRST to see the drives. DO NOT use `search_files` on your first turn!
   a) EXTENSION-FIRST TARGETING (HIGHLY RECOMMENDED): Before blindly searching, use your reasoning (or `extension_search`/`list_extension`) to decide EXACTLY which file extensions you need. Many tools (`list_dir`, `search_files`) natively support an `extensions` array parameter (e.g., `['.pdf', '.docx']`). 
      - ALWAYS use the `extensions` parameter when searching or listing! It instantly drops irrelevant files, drastically improving speed, boosting accuracy, and preventing massive context explosions.
      - **CRITICAL**: When using the `extensions` parameter in `list_dir`, you SHOULD drastically increase the `max_depth` to 5-10. Filtering makes deep recursive searches extremely cheap and safe!
   b) Survey the land: Use `list_dir` with a `max_depth` of 3 or 4 to quickly discover deep folder structures in one turn.
   c) Target by Structure: If you only want to know what subdirectories exist without cluttering context with files, run `list_dir` with `directories_only` set to true.
   d) Metadata RAG: If `search_files` still finds hundreds of files even after extension filtering, it will automatically perform "Metadata RAG" to semantically rank and return only the best matches!
5. SEMANTIC SEARCH: Use the `semantic_search` capability when you need specific conceptual context from INSIDE a large file.

You MUST return a JSON object with this EXACT structure:
{{
  "thought": "Evaluate the Goal, Working Memory, and Raw Tool Outputs.",
  "next_plan": "Explicitly state your next logical move based on your memory and raw tool outputs.",
  "output_document_append": "Any new markdown text to append to the continuous Output Document. Use this to format data/answers for the user.",
  "memory_updates": {{
    "key": "Internal planning fact or state variable to save in Working Memory (DO NOT put large data here)"
  }},
  "new_tasks": [
    {{
      "task_id": "unique_task_id",
      "capability_name": "name of capability",
      "inputs": {{"param_name": "param_value"}},
      "dependencies": ["list_of_parent_task_ids_that_must_complete_first"],
      "priority": 1
    }}
  ],
  "is_task_complete": false,
  "final_response": "If is_task_complete is true, provide final answer",
  "render_actions": [
    {{
      "type": "dataset",
      "object_id": "OBJ_17"
    }}
  ]
}}

Rules:
1. Do not include any text outside of the JSON object. DO NOT generate <think> blocks.
2. DEPENDENCIES: You can create a capability and immediately create a dependent capability that must wait for the first to complete by defining it in `dependencies`.
3. GOAL COMPLETION: Set `is_task_complete` to true and include `render_actions` if the data graph fully satisfies the user.

*** CRITICAL RULES FOR PATHS & DIRECTORIES (READ CAREFULLY) ***
4. NEVER GUESS PATHS: You are operating on a WINDOWS machine. You are strictly forbidden from guessing paths like `C:\\Users\\user` or `C:\\Users\\default`. YOU MUST EXPLORE THE DISK FIRST using `list_dir`.
5. NO VARIABLE SUBSTITUTION: The tools do not evaluate variables. If you know the username is `abhij` from your memory, you must literally type `C:\\Users\\abhij\\Documents`.
6. STRICT PATH PROVENANCE: You CANNOT hallucinate a directory. You can ONLY use a directory path in `search_files` or `list_dir` if you have PHYSICALLY SEEN that exact absolute path returned in your Raw Tool Outputs (e.g. from a previous `list_dir`). If you don't know the exact path, run `list_dir` to find it!
"""

        user_prompt = f"Goal: {context.goal}\n"
        user_prompt += f"Turn: {context.turn_count}\n\n"
        
        user_prompt += "--- CURRENT TASK GRAPH ---\n"
        user_prompt += f"{json.dumps(context.task_graph, indent=2)}\n\n"
        
        user_prompt += "--- OUTPUT DOCUMENT STATE ---\n"
        user_prompt += f"{context.output_document}\n\n"
        
        user_prompt += "--- WORKING MEMORY ---\n"
        user_prompt += f"{json.dumps(context.working_memory, indent=2)}\n\n"
        
        user_prompt += "--- RAW TOOL OUTPUTS (FROM LAST STEP) ---\n"
        user_prompt += f"{context.perceived_insights}\n\n"
        
        if context.failed_tasks:
            user_prompt += "--- FAILED TASKS (DO NOT RETRY THE SAME APPROACH) ---\n"
            user_prompt += f"{json.dumps(context.failed_tasks, indent=2)}\n"
            user_prompt += "IMPORTANT: The above tasks FAILED. Do NOT repeat them with the same inputs. Try a DIFFERENT approach or capability.\n\n"
        
        req = InferenceRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0
        )
        
        logger.info(f"Starting inference for turn {context.turn_count} of goal: {context.goal}")
        response = self._engine.generate(req)
        content = self._clean_json(response.content)
        
        # Fix unescaped Windows paths in JSON before parsing
        content = re.sub(r'(?<!\\)\\([^"\\/bfnrt])', r'\\\\\1', content)
        
        # Robust 3-layer Parsing for Unconstrained LLM JSON
        try:
            plan_data = json.loads(content, strict=False)
        except json.JSONDecodeError as e:
            # Fallback 1: PyYAML (handles single quotes and unquoted keys)
            try:
                import yaml
                plan_data = yaml.safe_load(content)
            except Exception:
                # Fallback 2: Python AST (handles single quotes natively)
                try:
                    import ast
                    content_py = content.replace("true", "True").replace("false", "False").replace("null", "None")
                    plan_data = ast.literal_eval(content_py)
                except Exception:
                    raise e
                    
        return GraphUpdate.model_validate(plan_data)

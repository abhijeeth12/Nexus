"""Nexus V2 CLI (Workflow Operating System Kernel Loop)."""

import os
import time
from rich.console import Console
from rich.prompt import Prompt

from kernel.event_bus import EventBus
from kernel.state_manager import InMemoryObjectStore, InMemoryHistoryStore
from kernel.scheduler import EventDrivenScheduler
from kernel.worker import LocalWorkerPool, LocalResourceManager
from kernel.executor import CapabilityExecutor
from kernel.compiler import WorkflowCompiler
from kernel.registry import CapabilityRegistry
from presentation.render_engine import RenderEngine

from planner.live_planner import LivePlanner, PlannerContext
# Use Local LLM (Ollama)
from infrastructure.inference.ollama_engine import OllamaInferenceEngine
from core.interfaces.inference import IInferenceEngine, InferenceRequest, InferenceResponse

from infrastructure.tools.terminal.run_command_tool import RunCommandTool
from infrastructure.tools.file.read_tool import ReadFileTool
from infrastructure.tools.file.list_dir_tool import ListDirTool
from infrastructure.tools.file.search_tool import SearchFileTool
from infrastructure.tools.file.write_tool import WriteFileTool
from infrastructure.tools.code.ast_tool import ReadAstTool
from infrastructure.tools.file.extension_search_tool import ExtensionSearchTool
from infrastructure.tools.file.list_extensions_tool import ListExtensionsTool
from infrastructure.tools.file.semantic_search_tool import SemanticSearchTool
from kernel.registry import CapabilityRegistry, LegacyToolAdapter

console = Console()

def main() -> None:
    console.print("[bold cyan]Nexus V2 Kernel Starting...[/bold cyan]")
    
    # 1. Initialize Kernel Subsystems
    event_bus = EventBus()
    object_store = InMemoryObjectStore()
    history_store = InMemoryHistoryStore()
    resource_manager = LocalResourceManager()
    
    registry = CapabilityRegistry()
    working_memory = {}
    
    # Load all standard tools into V2 Kernel via Adapter
    for legacy_tool in [
        RunCommandTool(), 
        ReadFileTool(), 
        ListDirTool(), 
        SearchFileTool(), 
        WriteFileTool(), 
        ReadAstTool(),
        ExtensionSearchTool(),
        ListExtensionsTool(),
        SemanticSearchTool()
    ]:
        registry.register_plugin(LegacyToolAdapter(legacy_tool))
    
    executor = CapabilityExecutor(registry, object_store, history_store, event_bus, working_memory)
    worker_pool = LocalWorkerPool(executor, event_bus)
    
    scheduler = EventDrivenScheduler(event_bus, object_store, worker_pool, resource_manager)
    compiler = WorkflowCompiler(registry)
    render_engine = RenderEngine(event_bus, object_store)
    
    def on_task_failed(event):
        console.print(f"[bold red]Task Failed:[/bold red] {event.metadata.get('task_id')} - {event.metadata.get('error')}")
    event_bus.subscribe("TaskFailed", on_task_failed)

    def on_task_completed(event):
        task_id = event.metadata.get('task_id')
        execution_id = event.metadata.get('execution_id')
        console.print(f"[bold green]Task Completed:[/bold green] {task_id}")
        # Find objects written by this execution
        written = [o for o in object_store.list_objects() if o.producer_execution_id == execution_id]
        if written:
            console.print(f"[bold blue]↳ Output to ObjectStore:[/bold blue] {len(written)} object(s)")
            for obj in written:
                content = getattr(obj, 'content', None) or getattr(obj, 'records', None)
                if content:
                    summary = str(content)[:200] + ("..." if len(str(content)) > 200 else "")
                    console.print(f"  [dim]Type: {obj.object_type}, Content Summary: {summary}[/dim]")
    event_bus.subscribe("TaskCompleted", on_task_completed)
    
    # Init Planner with Local LLM (Ollama)
    inference_engine = OllamaInferenceEngine(default_model="qwen2.5:7b")
    planner = LivePlanner(inference_engine)
    
    console.print("[bold green]Kernel Initialized. Ready for User Input.[/bold green]")
    
    try:
        while True:
            user_input = Prompt.ask("\n[bold green]>[/bold green]")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            turn_count = 1
            is_complete = False
            working_memory.clear()
            object_store.clear()
            scheduler.clear()
            
            output_document = ""
            last_plan = ""
            perceived_object_ids = set()
            global_insights_history = []
            
            import uuid
            session_workflow_id = str(uuid.uuid4())
            consecutive_failures = 0
            
            while not is_complete and turn_count < 10:
                with console.status(f"[bold blue]Planner (Turn {turn_count})...[/bold blue]"):
                    # Dump state
                    task_graph_dump = {}
                    failed_tasks_context = []
                    for g in scheduler.graphs.values():
                        for k, v in g.nodes.items():
                            task_graph_dump[k] = v.model_dump(mode='json')
                            # Collect failed task details for the planner
                            if v.state.value == "FAILED":
                                # Find the error from history
                                exec_record = history_store.get_execution(k)
                                error_msg = getattr(exec_record, 'exception', 'Unknown error') if exec_record else 'Unknown error'
                                failed_tasks_context.append({
                                    "task_id": k,
                                    "capability": v.capability_name,
                                    "inputs": v.inputs,
                                    "error": error_msg
                                })
                    
                    data_graph = []
                    for o in object_store.list_objects():
                        d = {
                            "task_id": getattr(o, "producer_execution_id", "UNKNOWN"),
                            "object_type": o.object_type,
                        }
                        
                        content = getattr(o, 'content', None) or getattr(o, 'records', None)
                        if isinstance(content, str):
                            try:
                                import json
                                parsed = json.loads(content)
                                if isinstance(parsed, list):
                                    d["data_type"] = "List"
                                    d["length"] = len(parsed)
                                elif isinstance(parsed, dict):
                                    d["data_type"] = "Dictionary"
                                    d["length"] = len(parsed)
                                else:
                                    d["data_type"] = "String"
                                    d["length"] = len(content)
                            except Exception:
                                d["data_type"] = "String"
                                d["length"] = len(content)
                        elif isinstance(content, list):
                            d["data_type"] = "List"
                            d["length"] = len(content)
                        elif isinstance(content, dict):
                            d["data_type"] = "Dictionary"
                            d["length"] = len(content)
                            
                        if content:
                            summary = str(content)
                            d["preview"] = summary[:200] + ("..." if len(summary) > 200 else "")
                            
                        data_graph.append(d)
                    
                    # Perception Phase
                    raw_outputs_for_perception = []
                    for o in object_store.list_objects():
                        if o.object_id not in perceived_object_ids:
                            content = getattr(o, 'content', None) or getattr(o, 'records', None)
                            raw_outputs_for_perception.append({
                                "task_id": getattr(o, "producer_execution_id", "UNKNOWN"),
                                "object_type": o.object_type,
                                "content": content
                            })
                            perceived_object_ids.add(o.object_id)
                            
                    perceived_insights = ""
                    if raw_outputs_for_perception:
                        import json
                        perceived_insights = json.dumps(raw_outputs_for_perception)
                    
                    context = PlannerContext(
                        goal=user_input,
                        turn_count=turn_count,
                        task_graph=task_graph_dump,
                        data_graph_summaries=data_graph,
                        working_memory=working_memory,
                        output_document=output_document,
                        perceived_insights=perceived_insights,
                        failed_tasks=failed_tasks_context
                    )
                    
                    try:
                        graph_update = planner.plan(context, registry)
                    except Exception as e:
                        console.print(f"[bold red]Planner Error:[/bold red] {e}")
                        break
                        
                if getattr(graph_update, "thought", ""):
                    console.print(f"\n[bold cyan]Thought:[/bold cyan] {graph_update.thought}")
                    
                if getattr(graph_update, "next_plan", ""):
                    last_plan = graph_update.next_plan
                    console.print(f"[bold cyan]Next Plan:[/bold cyan] {last_plan}")
                    
                if getattr(graph_update, "output_document_append", ""):
                    append_text = graph_update.output_document_append
                    output_document += append_text + "\n"
                    from rich.panel import Panel
                    from rich.markdown import Markdown
                    console.print(Panel(Markdown(output_document), title="Continuous Output Document", border_style="green"))
                    
                if getattr(graph_update, "memory_updates", None):
                    updates = getattr(graph_update, "memory_updates")
                    working_memory.update(updates)
                    context.working_memory.update(updates)
                    console.print(f"\n[bold yellow]Memory Updates:[/bold yellow]")
                    for k, v in updates.items():
                        console.print(f"  [yellow]- {k}:[/yellow] {v}")
                        
                # Append Planner's Synthesis to Global History instead of raw tool data
                turn_synthesis = f"Thought: {getattr(graph_update, 'thought', '')}\nMemory Updates: {getattr(graph_update, 'memory_updates', {})}"
                if turn_synthesis.strip():
                    global_insights_history.append(turn_synthesis)
                    
                if getattr(graph_update, "is_task_complete", False):
                    console.print(f"\n[bold green]Final Response:[/bold green] {getattr(graph_update, 'final_response', '')}")
                    # Issue render actions
                    for action in getattr(graph_update, "render_actions", []):
                        event_bus.publish(type('RenderAction', (), {'event_type': 'RenderAction', 'metadata': {'object_id': action.get('object_id')}})())
                    break
                    
                if getattr(graph_update, "new_tasks", []):
                    # Compile
                    new_tasks = getattr(graph_update, "new_tasks")
                    for t in new_tasks:
                        console.print(f"[bold magenta]Scheduled Capability:[/bold magenta] {t.get('task_id')} - {t.get('capability_name')}")
                        console.print(f"  [dim]Inputs: {t.get('inputs')}[/dim]")
                        
                    executable_graph = compiler.compile(new_tasks, workflow_id=session_workflow_id)
                    # Submit to Scheduler -> Triggers execution asynchronously
                    scheduler.submit_graph(executable_graph)
                    
                    # Wait for local worker thread time to process
                    while not scheduler.is_idle():
                        time.sleep(0.5)
                    
                    # Check if all new tasks failed — track consecutive failures
                    all_new_failed = all(
                        executable_graph.nodes[tid].state.value == "FAILED"
                        for tid in executable_graph.nodes
                    )
                    if all_new_failed:
                        consecutive_failures += 1
                        console.print(f"[bold red]⚠ All tasks failed this turn ({consecutive_failures}/3 consecutive failures)[/bold red]")
                        if consecutive_failures >= 3:
                            console.print("[bold red]Aborting: 3 consecutive turns of total failure. The planner cannot make progress.[/bold red]")
                            break
                    else:
                        consecutive_failures = 0
                        
                turn_count += 1
                
            # FINAL SYNTHESIZER LLM PHASE
            if global_insights_history:
                with console.status("[bold cyan]Synthesizing final response across all turns...[/bold cyan]"):
                    history_str = "\n\n".join(global_insights_history)
                    
                    if len(history_str) > 12000:
                        # Map-Reduce for infinite context handling
                        console.print("[dim]History is huge. Triggering Map-Reduce compression...[/dim]")
                        chunks = [history_str[i:i+10000] for i in range(0, len(history_str), 10000)]
                        reduced_chunks = []
                        for idx, chunk in enumerate(chunks):
                            map_prompt = f"Goal: {user_input}\n\nExtract and summarize all key facts related to the goal from this chunk:\n{chunk}"
                            req = InferenceRequest(system_prompt="You are a data compressor.", user_prompt=map_prompt, temperature=0.0)
                            resp = inference_engine.generate(req)
                            reduced_chunks.append(resp.content)
                        history_str = "\n\n".join(reduced_chunks)
                        
                    final_prompt = f"""You are the Final Synthesizer. 
User's Goal: {user_input}
Output Document (Partial Drafts): {output_document}
Global Insights History: {history_str}

Using the complete history of all insights gathered, generate a comprehensive, structured, and beautifully styled final markdown response for the user. Do not explain your process, just give the final answer."""
                    req = InferenceRequest(system_prompt="You are the Final Synthesizer.", user_prompt=final_prompt, temperature=0.3)
                    final_resp = inference_engine.generate(req)
                    
                from rich.panel import Panel
                from rich.markdown import Markdown
                console.print(Panel(Markdown(final_resp.content), title="Final Answer", border_style="bold green"))
                
    except KeyboardInterrupt:
        pass
    finally:
        console.print("[dim]Kernel Shutdown.[/dim]")

if __name__ == "__main__":
    main()

"""Render Engine for CLI UI."""
from core.interfaces.kernel import IEventBus, IObjectStore
from kernel.event_bus import BaseEvent
from rich.console import Console
from rich.table import Table
import logging

logger = logging.getLogger(__name__)
console = Console()

class RenderActionEvent(BaseEvent):
    event_type: str = "RenderAction"
    
class RenderEngine:
    def __init__(self, event_bus: IEventBus, object_store: IObjectStore) -> None:
        self.event_bus = event_bus
        self.object_store = object_store
        self.event_bus.subscribe("RenderAction", self.handle_render)
        
    def handle_render(self, event: BaseEvent) -> None:
        obj_id = event.metadata.get("object_id")
        if not obj_id: return
        
        obj = self.object_store.get_object(obj_id)
        if not obj:
            console.print(f"[red]RenderEngine: Object {obj_id} not found.[/red]")
            return
            
        if obj.object_type == "DatasetObject":
            table = Table(title=f"Dataset: {obj.object_id}")
            records = getattr(obj, "records", [])
            if records:
                headers = list(records[0].keys())
                for h in headers:
                    table.add_column(h, style="cyan")
                for rec in records:
                    table.add_row(*[str(rec.get(h, "")) for h in headers])
            console.print(table)
        elif obj.object_type == "SummaryObject":
            console.print(f"[bold cyan]Summary:[/bold cyan] {getattr(obj, 'content', '')}")
        else:
            console.print(f"[dim]RenderEngine: Unknown object type {obj.object_type}[/dim]")

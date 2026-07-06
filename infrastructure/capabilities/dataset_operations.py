"""Dataset Operations Semantic Capabilities."""

from typing import Any, Type, Dict, List
from pydantic import BaseModel, Field
import uuid
import time

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier
from core.models.workflow_objects import DatasetObject, CapabilityExecution

class FilterDatasetParams(BaseModel):
    dataset_id: str = Field(..., description="The ID of the dataset to filter (e.g., 'OBJ_17').")
    key: str = Field(..., description="The dictionary key in the records to filter on (e.g., 'size_bytes').")
    operator: str = Field(..., description="The operator: 'equals', 'contains', 'greater_than', 'less_than'.")
    value: Any = Field(..., description="The value to compare against.")

class FilterDatasetCapability(BaseTool):
    """Filters a WorkflowState DatasetObject and produces a new DatasetObject."""
    
    @property
    def name(self) -> str:
        return "filter_dataset"
        
    @property
    def description(self) -> str:
        return "Filters an existing dataset and yields a new dataset with the matching records."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return FilterDatasetParams
        
    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: FilterDatasetParams = parsed_kwargs
        workflow_state = getattr(context, "workflow_state", None)
        
        if not workflow_state:
            return ExecutionResult(success=False, error="WorkflowState not available.")
            
        source_dataset = workflow_state.objects.get(params.dataset_id)
        if not source_dataset or getattr(source_dataset, "type", "") != "DatasetObject":
            return ExecutionResult(success=False, error=f"Dataset {params.dataset_id} not found or invalid type.")
            
        filtered_records = []
        for record in getattr(source_dataset, "records", []):
            val = record.get(params.key)
            if val is None:
                continue
                
            match = False
            try:
                if params.operator == "equals" and val == params.value: match = True
                elif params.operator == "contains" and params.value in val: match = True
                elif params.operator == "greater_than" and float(val) > float(params.value): match = True
                elif params.operator == "less_than" and float(val) < float(params.value): match = True
            except:
                pass
                
            if match:
                filtered_records.append(record)
                
        execution_id = str(uuid.uuid4())
        new_dataset = DatasetObject(
            producer_capability=self.name,
            producer_execution_id=execution_id,
            parent_object_ids=[source_dataset.id],
            records=filtered_records
        )
        
        execution = CapabilityExecution(
            id=execution_id,
            capability_name=self.name,
            status="COMPLETED",
            parameters=parsed_kwargs.model_dump(),
            completed_at=new_dataset.created_at
        )
        
        workflow_state.executions[execution_id] = execution
        workflow_state.objects[new_dataset.id] = new_dataset
        workflow_state.object_summaries.append(new_dataset.summarize())
        
        return ExecutionResult(
            success=True, 
            output=f"Capability executed successfully. Filtered dataset '{new_dataset.id}' created with {len(filtered_records)} records.",
            metadata={"dataset_id": new_dataset.id}
        )

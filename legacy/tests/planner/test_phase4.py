"""Tests for Phase 4 components."""

import pytest
from core.models.instruction import Instruction, GraphUpdate
from planner.dummy_planner import DummyPlanner
from planner.schema_generator import SchemaGenerator
from agents.registry import CapabilityRegistry
from agents.file_agent import FileAgent

def test_instruction_schema_validation() -> None:
    # Verify Pydantic validates standard structures
    instr = Instruction(agent_name="agent_x", intent="do_y", parameters={"key": "val"})
    assert instr.agent_name == "agent_x"
    
    response = GraphUpdate(
        new_tasks=[{"id": "t1", "description": "do it", "instruction_agent": instr.agent_name, "instruction_intent": instr.intent, "instruction_parameters": instr.parameters}],
        is_task_complete=False
    )
    assert len(response.new_tasks) == 1

def test_schema_generator() -> None:
    registry = CapabilityRegistry()
    registry.register_agent(FileAgent())
    
    schema = SchemaGenerator.generate_registry_schema(registry)
    
    # Verify the schema correctly mapped the FileAgent capabilities
    assert "file_agent" in schema
    agent_caps = schema["file_agent"]
    assert "move_file" in agent_caps
    assert "read_file" in agent_caps
    
    # Verify parameter schemas are embedded correctly
    move_schema = agent_caps["move_file"]["parameters"]
    assert "source" in move_schema
    assert "destination" in move_schema

def test_dummy_planner() -> None:
    registry = CapabilityRegistry()
    planner = DummyPlanner()
    
    # Test 'move' intent extraction
    res1 = planner.plan("Please move this file", registry)
    assert res1.new_tasks[0]["instruction_intent"] == "move_file"
    
    # Test 'read' intent extraction
    res2 = planner.plan("Can you read this?", registry)
    assert res2.new_tasks[0]["instruction_intent"] == "read_file"
    
    # Test unknown
    res3 = planner.plan("Hack the mainframe", registry)
    assert len(res3.new_tasks) == 0

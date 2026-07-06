"""Tests for Terminal Agent."""

import pytest
from agents.terminal_agent import TerminalAgent
from core.models.tool_context import ToolContext

def test_terminal_agent_capabilities() -> None:
    agent = TerminalAgent()
    assert agent.name == "terminal_agent"
    caps = agent.get_capabilities()
    assert len(caps) == 5
    assert any(c.name == "run_command" for c in caps)

def test_terminal_agent_handle_instruction() -> None:
    agent = TerminalAgent()
    instr = {"intent": "run_command", "parameters": {"command": "echo test"}}
    tools_and_params = agent.handle_instruction(instr)
    assert len(tools_and_params) == 1
    
    tool, params = tools_and_params[0]
    assert tool.name == "run_command"
    assert params["command"] == "echo test"

def test_run_command_tool() -> None:
    agent = TerminalAgent()
    tool = [t for t in agent.get_capabilities() if t.name == "run_command"][0]
    ctx = ToolContext(transaction_id="tx-1", working_directory=".")
    
    # We test a simple echo command
    # Windows shell syntax
    res = tool.execute(ctx, **{"command": "echo hello", "timeout": 5})
    assert res.success is True
    # 'hello' should be in stdout
    assert "hello" in str(res.output).lower()

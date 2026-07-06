"""Tests for new file tools."""

import os
import pytest
from infrastructure.tools.file.write_tool import WriteFileTool
from infrastructure.tools.file.list_dir_tool import ListDirTool
from core.models.tool_context import ToolContext

from pathlib import Path

def test_write_file_tool(tmp_path: Path) -> None:
    tool = WriteFileTool()
    ctx = ToolContext(transaction_id="tx-1", working_directory=".")
    
    test_file = tmp_path / "test.txt"
    params = {"file_path": str(test_file), "content": "Hello World"}
    
    res = tool.execute(ctx, **params)
    assert res.success is True
    assert os.path.exists(test_file)
    with open(test_file, 'r') as f:
        assert f.read() == "Hello World"
        
    # Test Rollback
    tool.rollback(ctx)
    assert not os.path.exists(test_file)

def test_list_dir_tool(tmp_path: Path) -> None:
    tool = ListDirTool()
    ctx = ToolContext(transaction_id="tx-1", working_directory=str(tmp_path))
    
    # Create some dummy files
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    
    params = {"path": "."}
    res = tool.execute(ctx, **params)
    
    from typing import cast
    assert res.success is True
    out_str = str(res.output)
    assert "a.txt" in out_str
    assert "b.txt" in out_str


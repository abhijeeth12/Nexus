"""Tests for ReadFileTool."""

import pytest
from pathlib import Path

from infrastructure.tools.file.read_tool import ReadFileTool
from core.models.tool_context import ToolContext

def test_read_file_success(tmp_path: Path) -> None:
    """Verify reading an existing file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world", encoding="utf-8")
    
    tool = ReadFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, file_path="test.txt")
    assert result.success is True
    assert result.output == "hello world"

def test_read_file_not_found(tmp_path: Path) -> None:
    """Verify reading a non-existent file fails gracefully."""
    tool = ReadFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, file_path="does_not_exist.txt")
    assert result.success is False
    assert result.error is not None
    assert "File not found" in result.error

def test_read_file_is_directory(tmp_path: Path) -> None:
    """Verify reading a directory fails gracefully."""
    tool = ReadFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, file_path=str(tmp_path))
    assert result.success is False
    assert result.error is not None
    assert "not a file" in result.error

"""Tests for MoveFileTool."""

import pytest
from pathlib import Path

from infrastructure.tools.file.move_tool import MoveFileTool
from core.models.tool_context import ToolContext

def test_move_file_success_and_rollback(tmp_path: Path) -> None:
    """Verify moving a file and rolling it back."""
    src = tmp_path / "src.txt"
    src.write_text("content")
    dst = tmp_path / "dst.txt"
    
    tool = MoveFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    # Execute move
    result = tool.execute(ctx, source="src.txt", destination="dst.txt")
    assert result.success is True
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "content"
    
    # Execute rollback
    rb_result = tool.rollback(ctx)
    assert rb_result.success is True
    assert src.exists()
    assert not dst.exists()
    assert src.read_text() == "content"

def test_move_file_into_directory(tmp_path: Path) -> None:
    """Verify moving a file into a directory."""
    src = tmp_path / "src.txt"
    src.write_text("content")
    dst_dir = tmp_path / "dst_dir"
    dst_dir.mkdir()
    
    tool = MoveFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, source="src.txt", destination="dst_dir")
    assert result.success is True
    assert not src.exists()
    assert (dst_dir / "src.txt").exists()

def test_move_file_source_missing(tmp_path: Path) -> None:
    """Verify moving missing source fails."""
    tool = MoveFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, source="missing.txt", destination="dst.txt")
    assert result.success is False
    assert result.error is not None
    assert "Source not found" in result.error

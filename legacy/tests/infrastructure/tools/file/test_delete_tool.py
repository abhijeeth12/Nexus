"""Tests for DeleteFileTool."""

import pytest
from pathlib import Path

from infrastructure.tools.file.delete_tool import DeleteFileTool
from core.models.tool_context import ToolContext

def test_delete_file_success_and_rollback(tmp_path: Path) -> None:
    """Verify safely deleting a file and rolling it back."""
    target = tmp_path / "target.txt"
    target.write_text("content")
    
    tool = DeleteFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    # Execute delete
    result = tool.execute(ctx, file_path="target.txt")
    assert result.success is True
    assert not target.exists()
    
    trash_dir = tmp_path / ".nexus_trash" / "tx_1"
    assert trash_dir.exists()
    assert (trash_dir / "target.txt").exists()
    
    # Execute rollback
    rb_result = tool.rollback(ctx)
    assert rb_result.success is True
    assert target.exists()
    assert target.read_text() == "content"
    assert not (trash_dir / "target.txt").exists()

def test_delete_file_missing(tmp_path: Path) -> None:
    """Verify deleting missing file fails."""
    tool = DeleteFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, file_path="missing.txt")
    assert result.success is False
    assert result.error is not None
    assert "File not found" in result.error

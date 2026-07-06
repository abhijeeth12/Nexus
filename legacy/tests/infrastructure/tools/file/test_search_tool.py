"""Tests for SearchFileTool."""

import pytest
from pathlib import Path
from typing import List

from infrastructure.tools.file.search_tool import SearchFileTool
from core.models.tool_context import ToolContext

def setup_test_files(base_dir: Path) -> None:
    """Helper to create dummy files."""
    (base_dir / "doc1.txt").write_text("1")
    (base_dir / "image.png").write_text("img")
    
    sub = base_dir / "subdir"
    sub.mkdir()
    (sub / "doc2.txt").write_text("2")
    (sub / "other.log").write_text("log")

def test_search_file_recursive(tmp_path: Path) -> None:
    """Verify recursive search works."""
    setup_test_files(tmp_path)
    
    tool = SearchFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, query="doc")
    assert result.success is True
    
    output = result.output
    assert isinstance(output, list)
    assert len(output) == 2
    assert any("doc1.txt" in p for p in output)
    assert any("doc2.txt" in p for p in output)

def test_search_file_non_recursive(tmp_path: Path) -> None:
    """Verify non-recursive search works."""
    setup_test_files(tmp_path)
    
    tool = SearchFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, query="doc", recursive=False)
    assert result.success is True
    
    output = result.output
    assert isinstance(output, list)
    assert len(output) == 1
    assert "doc1.txt" in output[0]

def test_search_file_invalid_directory(tmp_path: Path) -> None:
    """Verify searching an invalid directory fails gracefully."""
    tool = SearchFileTool()
    ctx = ToolContext(transaction_id="tx_1", working_directory=str(tmp_path))
    
    result = tool.execute(ctx, query="doc", directory="invalid_dir")
    assert result.success is False
    assert result.error is not None
    assert "Invalid directory" in result.error

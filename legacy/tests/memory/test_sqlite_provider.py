"""Tests for SQLite Memory Provider."""

import pytest
from memory.providers.sqlite_provider import SQLiteMemoryProvider

@pytest.fixture
def sqlite_provider() -> SQLiteMemoryProvider:
    provider = SQLiteMemoryProvider(db_path=":memory:")
    return provider

def test_store_and_query_sqlite(sqlite_provider: SQLiteMemoryProvider) -> None:
    # Test storing facts
    fact1 = {"content": "User prefers dark mode", "metadata": {"source": "user_preference"}}
    fact2 = {"content": "Project directory is /src", "metadata": {"source": "context"}}
    
    assert sqlite_provider.store(fact1) is True
    assert sqlite_provider.store(fact2) is True
    
    # Test querying
    results = sqlite_provider.query("dark mode")
    assert len(results) == 1
    assert results[0]["content"] == "User prefers dark mode"
    assert results[0]["metadata"]["source"] == "user_preference"
    
    # Test missing content
    assert sqlite_provider.store({"metadata": {}}) is False

def test_sqlite_provider_name(sqlite_provider: SQLiteMemoryProvider) -> None:
    assert sqlite_provider.name == "sqlite_short_term"

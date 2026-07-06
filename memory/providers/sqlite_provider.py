"""SQLite Memory Provider."""

import sqlite3
import json
from typing import Any, Dict, List
from pathlib import Path

from core.interfaces.memory import IMemoryProvider
from memory.interfaces.storage import IKeywordIndex, ISessionStore
from memory.models import Chunk
import uuid

class SQLiteMemoryProvider(IMemoryProvider, ISessionStore):
    """
    Short-Term Memory implementation using SQLite.
    Stores conversation history and short-term facts.
    """
    
    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._initialize_schema()
        
    @property
    def name(self) -> str:
        return "sqlite_short_term"
        
    def _initialize_schema(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memory_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    metadata TEXT NOT NULL,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_request TEXT NOT NULL,
                    transaction_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    success BOOLEAN,
                    tool_executions TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );
                """
            )
            
    def query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Simple keyword-based retrieval for short-term memory.
        In a real scenario, this might use FTS (Full Text Search) in SQLite.
        """
        cursor = self._conn.cursor()
        # Basic LIKE search for demonstration
        cursor.execute(
            "SELECT content, metadata FROM memory_facts WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        results = []
        for row in cursor.fetchall():
            results.append({
                "content": row["content"],
                "metadata": json.loads(row["metadata"])
            })
        return results

    def store(self, fact: Dict[str, Any]) -> bool:
        """Stores a fact with optional metadata."""
        content = fact.get("content")
        if not content:
            return False
            
        metadata = fact.get("metadata", {})
        
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO memory_facts (content, metadata) VALUES (?, ?)",
                    (content, json.dumps(metadata))
                )
            return True
        except Exception:
            return False
            
    def store_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO sessions (id, metadata) VALUES (?, ?)",
                (session_id, json.dumps(metadata))
            )
            
    def store_interaction(self, interaction_data: Dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO interactions (id, session_id, user_request, transaction_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                (interaction_data["id"], interaction_data["session_id"], interaction_data["user_request"], 
                 interaction_data.get("transaction_id"), interaction_data.get("timestamp"))
            )
            
    def store_transaction(self, transaction_data: Dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO transactions (id, session_id, goal, success, tool_executions, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (transaction_data["id"], transaction_data["session_id"], transaction_data["goal"],
                 transaction_data["success"], json.dumps(transaction_data.get("tool_executions", [])), 
                 transaction_data.get("timestamp"))
            )
            
    def get_recent_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "goal": row["goal"],
                "success": bool(row["success"]),
                "tool_executions": json.loads(row["tool_executions"]),
                "timestamp": row["timestamp"]
            })
        return results[::-1]  # Return in chronological order
            
    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

class SQLiteKeywordIndex(IKeywordIndex):
    """Adapts SQLiteMemoryProvider to act as an IKeywordIndex."""
    def __init__(self, provider: SQLiteMemoryProvider) -> None:
        self._provider = provider
        
    def search(self, keyword: str, limit: int = 5) -> List[Chunk]:
        results = self._provider.query(keyword, limit)
        chunks = []
        for r in results:
            meta = r.get("metadata", {})
            chunks.append(Chunk(
                id=meta.get("chunk_id", str(uuid.uuid4())),
                document_id=meta.get("document_id", "unknown"),
                content=r.get("content", ""),
                metadata=meta
            ))
        return chunks

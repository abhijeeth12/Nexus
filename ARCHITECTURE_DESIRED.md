# Nexus Desired Architecture Blueprint

This document outlines the target architectural state for the Nexus Intelligent Agentic Operating Layer. It serves as the guiding blueprint for development, ensuring all new features align with the core philosophy and that architectural decisions are not lost.

## 1. Core Philosophy

* **Operating System Isolation**: The filesystem is a source of truth, but never a direct retrieval engine. Nexus continuously maintains an indexed representation of the OS. The Planner communicates *only* with the Memory Service.
* **Orchestration Flow**: `User -> Planner -> MemoryService (context) -> Planner (instruction) -> Orchestrator -> Agents -> Execution Engine -> OS`.
* **Replaceable Components**: Every major component (Agents, Planners, Memory Providers, Embeddings) is isolated behind strict interfaces and must remain independently replaceable.
* **Deterministic Execution**: LLMs only reason and plan. Execution is 100% deterministic via the Command Pattern (Tools).

## 2. Memory & Retrieval Subsystem (The Knowledge Engine)

The Memory Service is not just a database; it is a full Knowledge Retrieval Engine that models the user's entire computing environment.

### MemoryService Facade
The `MemoryService` remains the *only* public interface for context retrieval. Internally, it coordinates:
* **Short-Term Memory**: Conversation history and active transactions.
* **Retrieval Engine**: The core subsystem for fetching OS knowledge.

### The Stateful Retrieval Engine
GraphRAG is no longer the sole memory paradigm. The Retrieval Engine operates in a localized, context-aware loop consisting of:

1. **Working Memory**: A short-term key-value store where the Main Planner explicitly tracks variables and project structures.
2. **Perception Engine Filtering**: Before raw tool outputs (e.g., from reading a file) hit the Main Planner, they are routed through the `Perception Engine`. This LLM uses the current `Working Memory` and `Last Plan` to aggressively filter noise and extract only highly relevant `Perceived Insights`.
3. **Localized Semantic Search (RAG)**: When dense, conceptual searching is required, the Planner invokes the `semantic_search` tool. This tool reads a specific file, chunks it, and uses local vector embeddings (e.g., via Ollama `nomic-embed-text`) to perform cosine similarity. It returns only the Top K most relevant chunks, bypassing expensive whole-system vector queries.
4. **Continuous Output Document**: The Main Planner maintains a continuous markdown output buffer, allowing it to slowly piece together the final answer to the user over multiple retrieval loops.

## 3. Data Abstractions

### Stable Document Identity
Files are never identified solely by their file path, as paths can change. Every indexable resource has a stable internal `Document ID`. The file path is simply metadata attached to the ID.

### The Document & Chunk Model
* **Document**: The highest-level representation of an OS resource. Contains `Document ID`, `Content`, `Metadata` (extensively rich, e.g., MIME type, checksum, workspace, tags, creation time), `Source`, and `Version`.
* **Chunk**: Documents are never embedded directly. They are broken into `Chunks`, which are the smallest retrievable semantic units. Chunks maintain references to their parent `Document ID`, sibling chunks, hierarchy path, and their specific embedding vector.

## 4. The Ingestion Pipeline

Ingestion is strictly decoupled into independent stages:

`Filesystem Event -> Document Update -> Chunker -> Embedding Provider -> Vector Store / Graph Update -> MemoryService`

* **Background Indexer**: A local filesystem watcher (`watchdog`) that asynchronously feeds events into the ingestion pipeline without blocking the user interface.
* **IChunker**: Modular chunking strategies (Plain Text, Markdown, PDF, Code).
* **IEmbeddingProvider**: Separates embedding generation (e.g., SentenceTransformers, OpenAI) from storage.
* **Vector Store**: Only responsible for storing, updating, deleting, and similarity searching vectors (e.g., ChromaDB, Qdrant). It *never* generates embeddings itself.
* **Knowledge Graph**: Stores relationships, not embeddings. Models interactions like `Folder contains File`, `Document references Document`, or `Project contains Code`. Hierarchy is represented via relationships, not file paths.

## 5. Long-Term Vision

The Knowledge Retrieval Engine is entirely generic. While currently focused on files, it is architected to eventually ingest and retrieve context from Emails, Browser History, Terminal Sessions, Calendar Events, and generic Workflows. It is an operating system retrieval engine, not just a document indexer.

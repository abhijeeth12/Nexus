# Nexus Intelligent Agentic Operating Layer
## Complete Architecture Reference

This document serves as the primary developer reference for the Nexus platform. It describes the complete architecture as it is implemented today. Nexus is built on strict principles of Domain-Driven Design, deterministic execution, and highly decoupled knowledge retrieval.

---

## 1. Core Philosophy

1. **OS as Source of Truth, Not Retrieval Engine**: The filesystem is never searched directly during user queries. Nexus maintains a continuous, indexed representation of the OS inside its Memory Subsystem.
2. **Deterministic Execution**: LLMs (via the Planner) are strictly confined to reasoning and generating JSON plans. They never execute code directly. Execution is guaranteed to be deterministic, leveraging the Command Pattern (`ITool`) wrapped in atomic transactions.
3. **Decoupled Knowledge**: Ingestion and Retrieval are completely independent pipelines. The `MemoryService` facade hides all storage complexity (SQLite, ChromaDB, NetworkX) from the Orchestration layer.

---

## 2. Orchestration & Execution Flow

The primary flow of Nexus handles translating natural language into safe, transactional Operating System actions via a Stateful Iterative Loop.

### Flow
`User -> CLI -> Perception Engine -> Planner -> Orchestrator -> OS -> Object Store -> Loop Back`

### Components
* **Perception Engine**: An LLM filter that sits between raw OS outputs and the Planner. It synthesizes raw data into `Perceived Insights` based on the user's goal, the last plan, and current working memory.
* **Planner (`LivePlanner`)**: Generates a deterministic 4-Pillar JSON response: `thought`, `next_plan`, `output_document_append` (for the user), and `new_tasks` (tool execution). It maintains its own `Working Memory` explicitly.
* **Capability Registry**: Dynamically injects Pydantic schemas of available Tools into the Planner's context.
* **Orchestrator (`nexus_cli.py` & `EventDrivenScheduler`)**: The central controller. It orchestrates the perception-planning loop, maintains the Output Document, and delegates task execution.
* **Agents (`IAgent`)**: Pure routing layers. They map abstract intent keys (e.g., `move_file`) to concrete `ITool` instances. They contain zero business logic.
* **Tools (`ITool`)**: Atomic operations (e.g., `MoveFileTool`, `ReadFileTool`). They encapsulate their own validation, execution, and rollback logic.
* **Execution Engine (`IExecutionEngine`)**: The sole gateway to the OS. Before executing a Tool, it checks for destructive intent via the `IApprovalProvider`. 
* **Transaction Manager**: Maintains a LIFO stack of executed Tools. If a multi-tool plan fails midway, the Engine calls `TransactionManager.rollback()`, ensuring the OS remains in a clean state.

---

## 3. The Memory Subsystem (Knowledge Engine)

The Memory Subsystem is arguably the most complex component, operating via two strictly separated, one-way pipelines hidden behind the `IMemoryService`.

### A. The Ingestion Pipeline
Converts raw OS events into structured, indexed knowledge asynchronously.

`Filesystem Event -> Index Coordinator -> Parser Registry -> Document -> Chunker -> Embedding Provider -> MemoryService`

* **Index Coordinator**: Receives events from the filesystem watcher (`watchdog`). It checks checksums for incremental updates, handles retries, and updates `IndexingStatus` (Pending, Indexed, Failed).
* **Parser Registry**: Maps resource types (e.g., `text/plain`) to specific `IParser` implementations.
* **IChunker**: Breaks parsed `Document`s into semantic `Chunk` models.
* **IEmbeddingProvider**: Separated from storage; exclusively handles vector generation.
* **Incremental & Resilient**: If embeddings fail (e.g., rate limit), metadata is *still* saved to the `MemoryService`. The resource is simply marked for retry.

### B. The Retrieval Pipeline
A multi-strategy rank-fusion engine for fetching context without touching the filesystem.

`Query -> Query Analyzer -> Retrieval Planner -> Retrievers -> Rank Fusion -> Context Builder -> Planner`

* **Query Analyzer**: Heuristically (or via LLM) determines the nature of the query (e.g., "Find invoice.pdf" triggers keyword search; "Concepts in attention" triggers dense search).
* **Retrieval Planner**: Selects only the necessary `IRetriever` implementations based on the analyzer, minimizing latency.
* **Concrete Retrievers**: 
    - `DenseRetriever` (Semantic search via ChromaDB).
    - `GraphRetriever` (Structural traversal via NetworkX).
    - `KeywordRetriever` & `MetadataRetriever` (Exact match via SQLite).
* **Candidates & Rank Fusion**: All retrievers return strongly-typed `Candidate` objects containing the chunk, document metadata, and `retrieval_evidence`. The engine fuses these results using `ReciprocalRankFusion` (RRF).
* **Context Builder**: Formats the final fused candidates into a dense, token-optimized context string for the Planner.

---

## 4. Data Abstractions & Stable Identity

* **Stable Identity**: Files are never identified by paths, which are mutable. Every resource receives a stable internal UUID.
* **Resource**: The base model for any OS entity (File, Repo, Email). Tracks `checksum`, `version`, and `indexing_status`.
* **Document**: The parsed textual representation of a Resource.
* **Chunk**: The smallest retrievable semantic unit, containing an embedding and a reference to its parent Document.
* **Candidate**: The retrieval envelope containing the chunk and explainable `retrieval_evidence`.

---

## 5. Storage Providers (The Backends)

* **IVectorStore** (e.g., `ChromaVectorStore`): Exclusively stores vectors and performs similarity searches. It *never* generates embeddings.
* **IGraphStore** (e.g., `NetworkXGraphStore`): Exclusively stores node relationships and enables neighbor traversal.
* **IMetadataStore** & **IKeywordIndex**: SQLite-backed stores for handling non-dense attributes and exact string matching.

---

## 6. Directory Structure

* `/agents` - Routing logic and capability mapping.
* `/api` - FastAPI headless interface.
* `/core` - Abstract interfaces (`IAgent`, `ITool`, `IMemoryService`), base classes, and DI Container.
* `/engine` - Execution Engine, Transaction Manager, and Approval Middleware.
* `/infrastructure` - Low-level OS integrations (File Tools, Watchdog indexer).
* `/memory` - The entire Knowledge Engine (Ingestion, Retrieval, Models, Providers).
* `/planner` - LLM interaction and Schema generation.
* `/tests` - Mirrored structure containing comprehensive `pytest` suites.

## 7. Current State & Next Steps
The architecture is 100% stable, fully decoupled, heavily tested, and strictly typed via `mypy`. All major pipelines (Orchestration, Ingestion, Retrieval) are implemented via concrete, extensible classes. The next era of development involves purely building out new Tools, new Parsers, and integrating the live OpenAI `IPlanner`.

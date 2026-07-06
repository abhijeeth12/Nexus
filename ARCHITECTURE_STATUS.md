# Nexus Architecture Status

This document provides a comprehensive overview of the current state of the Nexus Intelligent Agentic Operating Layer. It is based *strictly* on the codebase as it exists today, distinguishing clearly between what is implemented, partially implemented, and planned.

## 1. Implemented Components

The following components are fully implemented and integrated into the active system:

* **Dependency Injection Container**: `NexusContainer` (`core/di/container.py`) manages component lifecycles.
* **Telemetry**: `JsonFormatter` and `get_logger()` (`core/telemetry/logger.py`) provide JSON structured logging with trace IDs.
* **Atomic Tools**: `ReadFileTool`, `SearchFileTool`, `MoveFileTool`, `DeleteFileTool` (`infrastructure/tools/file/`).
* **Execution Core**: `ExecutionEngine` (`engine/execution_engine.py`), `TransactionManager` (`engine/transaction.py`), and `MockApprovalProvider` (`engine/approval.py`).
* **Agent Layer**: `CapabilityRegistry` (`agents/registry.py`), `Orchestrator` (`agents/orchestrator.py`), and `FileAgent` (`agents/file_agent.py`).
* **Planner Layer**: `SchemaGenerator` (`planner/schema_generator.py`), `DummyPlanner` (`planner/dummy_planner.py`), and `LivePlanner` (`planner/live_planner.py`).
* **Inference Layer**: `IInferenceEngine`, `IModelManager`, `OllamaInferenceEngine`, `OllamaModelManager` (`infrastructure/inference/`).
* **Memory Subsystem - Models**: `Document`, `Chunk`, `Candidate`, `Resource` (`memory/models.py`).
* **Memory Subsystem - Ingestion**: `ParserRegistry`, `IndexCoordinator`, `IngestionPipeline` (`memory/ingestion/`).
* **Memory Subsystem - Retrieval**: `RetrievalEngine`, `RetrievalPlanner`, `ReciprocalRankFusion`, `DefaultContextBuilder` (`memory/retrieval/`).
* **Memory Subsystem - Facade**: `KnowledgeRetrievalService` (`memory/facade.py`).
* **Memory Subsystem - Concrete Retrievers**: `MetadataRetriever`, `KeywordRetriever`, `DenseRetriever`, `GraphRetriever`.
* **Memory Subsystem - Providers**: `SQLiteMemoryProvider`, `ChromaVectorStore`, `NetworkXGraphStore`.
* **API Layer**: FastAPI application (`api/main.py`) exposing `/capabilities`, `/plan`, and `/execute`.

## 2. Abstract Interfaces & Responsibilities

The system relies on strict interface contracts (`core/interfaces/` and `memory/interfaces/`):

* **`ITool`**: The atomic Command Pattern contract. Responsible for input schema exposure, validation, execution, and rollback.
* **`IAgent`**: Orchestration abstraction. Responsible for taking a JSON instruction and returning configured `ITool` instances. Contains no business logic.
* **`IExecutionEngine`**: The sole gateway to the OS. Responsible for executing tools, intercepting destructive actions via `SafetyTier`, and coordinating rollbacks.
* **`IPlanner`**: The AI reasoning abstraction. Responsible for translating natural language into a deterministic `ExecutionPlan`. Uses semantic scopes rather than platform-specific paths.
* **`IKnowledgeRetrievalService`**: The decoupled abstraction the Planner uses to request context.
* **`IInferenceEngine`**: The sole gateway to LLM inference across the system.
* **`IModelManager`**: Manages installed models, versioning, and downloads.
* **`IMemoryService`**: The facade for the entire knowledge engine.
* **`IApprovalProvider`**: Middleware interface for pausing execution to request user consent.
* **Storage Abstractions**: `IVectorStore`, `IGraphStore`, `IMetadataStore`, `IKeywordIndex`.

## 3. Concrete Implementations

* **`BaseTool` (Abstract Base)**: Implements common Pydantic validation and error handling for all tools.
* **Concrete Tools**: `MoveFileTool` and `DeleteFileTool` implement full `rollback()` capability by storing transaction-specific state.
* **`ExecutionEngine`**: Uses `TransactionManager` as a LIFO stack to automatically revert changes if a multi-step execution fails.
* **`FileAgent`**: Concretely maps abstract intent keys (e.g., `"move_file"`) to the correct `ITool` instances.
* **`OllamaInferenceEngine`**: Executes LLM interactions deterministically via local Ollama instances.

## 4. Execution Flow

The complete flow from CLI Request to OS Execution operates via a Stateful Iterative Loop:

1. **API/CLI Request**: User submits a natural language goal.
2. **Perception Phase**: The `Perception Engine` (an LLM) reads raw outputs from the previous turn, the user's goal, the last plan, and current working memory to generate `Perceived Insights`.
3. **Contextualization**: The system bundles the `Perceived Insights`, `Working Memory`, and `Output Document` state.
4. **Planning Phase**: The Main Planner (`LivePlanner`) evaluates this context against the `CapabilityRegistry` schema.
5. **JSON Generation**: The Planner returns a strict 4-Pillar JSON response: `thought`, `next_plan`, `output_document_append` (formatted output for the user), `memory_updates` (facts to remember), and `new_tasks` (tools to execute).
6. **Execution Orchestration**: The `EventDrivenScheduler` orchestrates the execution of `new_tasks` via the `CapabilityExecutor`.
7. **Tool Execution**: Atomic tools (e.g., `semantic_search`, `read_file`) run deterministically.
8. **Loop**: The outputs are committed to the `InMemoryObjectStore`, and the loop returns to Step 2 until `is_task_complete` is true.

## 5. Dependency Graph

* **`FastAPI`** depends on -> `NexusContainer` (DI).
* **`NexusContainer`** depends on -> `ExecutionEngine`, `TransactionManager`, `IApprovalProvider`.
* **`Orchestrator`** depends on -> `CapabilityRegistry` and `IExecutionEngine`.
* **`ExecutionEngine`** depends on -> `ITool` and `TransactionManager`.
* **`IAgent`** depends on -> `ITool`.
* **`IPlanner`** depends on -> `IInferenceEngine` and `CapabilityRegistry`.
* **`LivePlanner`** depends on -> `IInferenceEngine` and `IKnowledgeRetrievalService`.

## 6. Folder Structure

* `agents/`: Contains capability mapping, routing logic, and orchestrators.
* `api/`: FastAPI routes, Pydantic HTTP models, and DI dependency injection wrappers.
* `core/`: The absolute center of the Domain-Driven Design. Holds `interfaces/`, `models/`, and `telemetry/`.
* `engine/`: The transactional boundary. Houses the Execution Engine, Approvals, and Rollback tracking.
* `infrastructure/`: Low-level implementations of tools (e.g., `shutil` wrappers) and inference clients (`OllamaInferenceEngine`).
* `memory/`: Houses memory backend implementations (Ingestion, Retrieval, Stores).
* `planner/`: LLM abstraction layer and DSL schema generation.
* `tests/`: 100% mirrored structure containing `pytest` suites.

## 7. Technologies Used

* **Python 3.13** (Strict `mypy` typing enforced)
* **Pydantic**: Deeply integrated for Input Schema validation and DSL generation.
* **dependency-injector**: Core component wiring.
* **FastAPI / Uvicorn**: Headless API serving.
* **pytest**: Testing framework.
* **sqlite3**: Short-term and Metadata memory storage.
* **chromadb**: Dense vector storage.
* **networkx**: Graph relationship storage.
* **watchdog**: OS filesystem observer.
* **ollama**: Local LLM inference.

## 8. Partially Implemented & Interface-Only Components

* **`IApprovalProvider`**: Currently only implemented via a `MockApprovalProvider` (always returns True). The actual UI-blocking implementation is pending Phase 7.
* **Background Indexer Daemon**: The coordinator and pipeline are built, but the actual daemonized thread watching a folder hasn't been instantiated yet.

## 9. Planned but Not Implemented Components

* **GUI / Frontend Integration**: The core relies on API or CLI currently; future graphical clients are pending.

## 10. Current Limitations

* The Approval Layer instantly approves destructive operations because there is no human-in-the-loop UI yet.
* Context is currently isolated per-transaction via `ToolContext`. There is no persistent session identity across API calls.
* Memory retrieval and ingestion pipelines are built and tested but haven't been tied directly to a live background daemon running alongside the API.

## 11. Upcoming Responsibilities of Phase 7

Phase 7 focuses entirely on bringing Nexus to life on the local machine as a usable prototype.

1. **Context Wiring**: Give the `LivePlanner` a brain by hooking it up to the Memory Subsystem.
2. **Real World Tooling**: Ensure `FileAgent` tools are flawless, and implement `TerminalAgent`.
3. **Interactive CLI**: Provide a beautiful, continuous user interface for interacting with the system, handling approvals, and viewing Execution Plans.

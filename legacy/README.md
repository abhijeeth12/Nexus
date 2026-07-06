# Legacy V1 Code

This directory contains files from the V1 agent-based architecture that are **no longer used** by the V2 Kernel loop (`nexus_cli.py`).

## Contents

- `agents/` — V1 agent classes (file_agent, code_agent, browser_agent, etc.) and the V1 `CapabilityRegistry`
- `validator.py` — V1 `PlanValidator` (references `ExecutionPlan` model)
- `scorer.py` — V1 `PlanQualityScorer` (references `ExecutionPlan` model)
- `schema_generator.py` — V1 `SchemaGenerator` (references V1 `CapabilityRegistry`)

## Why Moved

These files import V1-only types (`ExecutionPlan`, `agents.registry.CapabilityRegistry`) that do not exist in the V2 architecture. They would throw `ImportError` if any code path touched them. They have been quarantined here to keep the active codebase clean while preserving history.

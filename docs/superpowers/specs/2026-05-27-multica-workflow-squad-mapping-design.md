# Design Specification: Workflow → Multica Squad Mapping

This document outlines the design for adding workflow publishing support to the Multica adapter, mapping our core Workflow domain model to Multica's Squad concept. Multica uses prompt routing (squad instructions) rather than hard-coded workflow execution, so our rendered workflow markdown becomes the squad's instructions.

## Background and Goals

The system already supports syncing individual agent definitions to Multica via `multica agent create/update`. However, workflows (the orchestration layer that ties agents together) have no external publishing mechanism. Multica represents multi-agent orchestration through **squads** with **squad instructions** — the squad's prompt-based routing instructions tell the squad leader how to coordinate agents.

Goals:
1. **Add a `Workflow` domain model** — a lightweight publishing-oriented model alongside the existing `Agent` model.
2. **Define a `WorkflowPublisherPort`** — a domain-level port for publishing workflows, with no coupling to Multica concepts.
3. **Extend `MulticaAdapter`** — implement the port by mapping `Workflow` → `multica squad` CLI calls.
4. **Add a `sync-workflow` CLI command** — parse YAML, validate, render markdown, and publish.
5. **Add Makefile integration** — `make sync-workflow WORKFLOW=...`.

---

## Core Domain Model

### `Workflow` (`src/core/domain/models.py`)

A first-class domain model for the publishable representation of a workflow. Follows the same pattern as the existing `Agent` model.

```python
@dataclass(frozen=True)
class Workflow:
    id: str                  # workflow.name from YAML (e.g. "product-squad")
    instructions: str        # Rendered markdown — the full workflow instructions
    description: Optional[str] = None
```

The `instructions` field contains the rendered markdown output of the workflow YAML — the same content that `render_markdown()` produces. This is what becomes the squad's prompt routing instructions in Multica.

---

## Port (Interface)

### `WorkflowPublisherPort` (`src/core/ports/workflow_publisher.py`)

```python
from abc import ABC, abstractmethod
from src.core.domain.models import Workflow

class WorkflowPublisherPort(ABC):
    @abstractmethod
    def publish(self, workflow: Workflow) -> bool:
        """Publishes a workflow to the external system. Returns True on success."""
        pass
```

This port is intentionally domain-pure — no mention of squads, Multica, or any external concept. The adapter handles the translation.

---

## Adapter

### `MulticaAdapter` (`src/adapters/multica_adapter.py`)

`MulticaAdapter` will implement both `AgentPublisherPort` and `WorkflowPublisherPort`. The adapter is responsible for the conceptual mapping:

| Domain Concept | Multica Concept |
|---|---|
| `Workflow.id` | Squad name |
| `Workflow.instructions` | Squad instructions (prompt routing) |
| `Workflow.description` | Squad description |

#### Publish flow

1. **Check existence:** `multica squad get <workflow.id>`
2. **If exists (returncode 0):** Update the squad:
   ```bash
   multica squad update <workflow.id> --instructions <rendered_markdown> [--description <description>]
   ```
3. **If not found (returncode != 0):** Create the squad:
   ```bash
   multica squad create --name <workflow.id> --instructions <rendered_markdown> [--description <description>]
   ```

This mirrors the existing `publish()` pattern for agents (get → create or update).

---

## Service

### `WorkflowSyncService` (`src/core/services/workflow_sync_service.py`)

A lightweight service that coordinates the workflow publishing pipeline:

1. Load YAML data from file path.
2. Validate using existing `validate()` from `workflow_service.py`.
3. Render to markdown using existing `render_markdown()` from `markdown_renderer.py`.
4. Construct a `Workflow` domain model from the parsed data.
5. Publish via `WorkflowPublisherPort`.

```python
class WorkflowSyncService:
    def __init__(self, publisher: WorkflowPublisherPort):
        self.publisher = publisher

    def sync_workflow(self, yaml_path: str) -> bool:
        # Load, validate, render, build Workflow, publish
        ...
```

---

## CLI Command

### `sync-workflow` (`src/adapters/cli/entrypoint.py`)

New subcommand added to the existing CLI entrypoint:

```
python -m src.cli sync-workflow <yaml_path> [--adapter multica]
```

The command will:
1. Parse and validate the workflow YAML.
2. Render it to markdown instructions.
3. Build a `Workflow` domain model (id = `workflow.name`, instructions = rendered markdown, description = `workflow.description`).
4. Instantiate `MulticaAdapter` and invoke `publish()`.

---

## Makefile Integration

```makefile
sync-workflow: ## Validate + publish a workflow YAML as a squad to multica (usage: make sync-workflow WORKFLOW=workflow/product-squad.yaml)
	$(PYTHON) -m src.cli sync-workflow $(WORKFLOW)
```

Uses the existing `WORKFLOW` variable (default: `workflow/orchestrator-debate.yaml`).

---

## Files Summary

| Action | File |
|--------|------|
| MODIFY | `src/core/domain/models.py` — add `Workflow` dataclass |
| NEW | `src/core/ports/workflow_publisher.py` — `WorkflowPublisherPort` interface |
| MODIFY | `src/adapters/multica_adapter.py` — implement `WorkflowPublisherPort` (squad mapping) |
| NEW | `src/core/services/workflow_sync_service.py` — orchestration service |
| MODIFY | `src/adapters/cli/entrypoint.py` — add `sync-workflow` subcommand |
| MODIFY | `Makefile` — add `sync-workflow` target |

## Verification Plan

### Automated Tests
1. **`tests/test_multica_adapter.py`:** Add tests for `publish()` with `Workflow` objects, mocking subprocess calls for `multica squad get/create/update`.
2. **`tests/test_workflow_sync_service.py`:** Test the sync service with a mocked publisher and valid/invalid YAML data.
3. **Regression:** Ensure all existing tests continue to pass.

### Manual Verification
1. Run `python -m src.cli sync-workflow workflow/product-squad.yaml` and verify correct subprocess commands are formulated.
2. Run `make sync-workflow WORKFLOW=workflow/product-squad.yaml` and verify the Makefile integration works.

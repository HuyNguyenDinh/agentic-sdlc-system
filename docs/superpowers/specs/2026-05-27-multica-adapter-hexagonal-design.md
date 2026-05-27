# Design Specification: Hexagonal Refactoring and Multica CLI Adapter

This document outlines the design for refactoring the existing IaC CLI (`src/`) to follow Hexagonal Architecture (Ports and Adapters) and introducing an output adapter to register agents in the Multica platform using the `multica` CLI.

## Background and Goals

The current repository contains an agentic SDLC system where workflows are declared in YAML files under `workflow/` and agent system prompts are written as Markdown files under `agents/`. The goal is to:
1. **Refactor** the Python codebase (`src/`) to follow a clean Hexagonal Architecture.
2. **Scan** the `agents/` directory recursively to discover all agent markdown files.
3. **Integrate** with the `multica` CLI directly to register/create discovered agents, completely bypassing intermediate scripts.

---

## Hexagonal Architecture Design

We decouple the core domain logic (Workflows and Agents) from the external technologies (the File System, CLI inputs, and the Multica platform).

### Directory Structure

```text
src/
├── core/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── models.py            # Pure business entities: Agent, Workflow, Step, etc.
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── agent_repository.py  # Port (Interface) for loading agents
│   │   └── agent_publisher.py   # Port (Interface) for registering/syncing agents
│   └── services/
│       ├── __init__.py
│       ├── agent_service.py     # Syncing logic, coordinating domain/ports
│       └── workflow_service.py  # Workflow validation/rendering service
├── adapters/
│   ├── __init__.py
│   ├── fs_agent_repository.py   # concrete fs loader: parses markdown frontmatter & text
│   ├── multica_adapter.py       # concrete multica CLI interface: invokes subprocesses
│   ├── markdown_renderer.py     # concrete workflow renderer
│   └── cli/
│       ├── __init__.py
│       └── entrypoint.py        # Driving adapter: parses argparse arguments and invokes services
└── cli.py                       # Thin wrapper pointing to src.adapters.cli.entrypoint
```

---

## Core Domain Models (`src/core/domain/models.py`)

We represent the business concept of an **Agent** as a first-class domain model:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class Agent:
    id: str                  # Unique slug e.g. "pm-agent"
    role: str                # e.g. "Squad Leader & Orchestrator"
    instructions: str        # System prompt parsed from markdown
    description: Optional[str] = None
```

We will also define clean domain models for `Workflow`, `Step`, and `KnowledgeSource` to model the validation and rendering logic.

---

## Ports (Interfaces)

### 1. `AgentRepositoryPort` (`src/core/ports/agent_repository.py`)
Defines how the application service requests to load agents from a source.
```python
from abc import ABC, abstractmethod
from src.core.domain.models import Agent

class AgentRepositoryPort(ABC):
    @abstractmethod
    def get_all_agents(self) -> list[Agent]:
        """Loads and returns all agents from the storage/source."""
        pass
```

### 2. `AgentPublisherPort` (`src/core/ports/agent_publisher.py`)
Defines how the application service publishes/registers agents to external systems.
```python
from abc import ABC, abstractmethod
from src.core.domain.models import Agent

class AgentPublisherPort(ABC):
    @abstractmethod
    def publish(self, agent: Agent) -> bool:
        """Publishes/Registers an agent in the external system. Returns True if successful."""
        pass
```

---

## concrete Adapters

### 1. `FSAgentRepository` (`src/adapters/fs_agent_repository.py`)
Scans the `agents/` folder recursively for `.md` files.
- **Name/ID derivation**: The base filename without extension is used as the `id` (e.g. `pm-agent.md` -> `pm-agent`).
- **Description / Role extraction**:
  - The script will read the markdown file.
  - If a frontmatter block or line like `**Role:**` or `### **Role**` or `# Product Lead Agent` exists, it will extract the role description.
  - Otherwise, it will fallback to using the file name or a simplified title.
- **Instructions**: The complete raw content of the markdown file acts as the agent's instructions.

### 2. `MulticaAdapter` (`src/adapters/multica_adapter.py`)
Executes the `multica` CLI commands via Python's `subprocess` module:
- It checks if `multica` is available on the path.
- It maps the `Agent` domain model fields to CLI arguments:
  ```bash
  multica agent create --name "<name>" --instructions "<instructions>" --description "<description>"
  ```
- If the agent already exists, it can use the `multica agent update` or try to re-create it. We will handle error cases gracefully (e.g. if the CLI fails or returns error codes).

---

## Verification and Testing Plan

### Automated Tests
1. **Unit tests for FSAgentRepository**: Mock files and folders to verify that the scanner recursively discovers `.md` files, parses roles, and correctly populates the `Agent` domain models.
2. **Mock tests for MulticaAdapter**: Mock the subprocess calls to `multica agent create` to ensure that standard outputs, error codes, and flags are correctly formatted and invoked.
3. **Regression tests for Schema**: Ensure existing `test_schema.py` is maintained and passes without any regression.

### Manual Verification
1. We will verify that running `python3 -m src.cli sync-multica` scans the files and triggers the correct CLI executions.

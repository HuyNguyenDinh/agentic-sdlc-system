# Sync Workflow to Multica Squad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable syncing of workflow YAML definitions to the Multica platform as squads using the rendered workflow markdown as squad coordination instructions.

**Architecture:** Extend Hexagonal Architecture by adding a Workflow domain model, a WorkflowPublisherPort, extending the MulticaAdapter to implement this port and execute multica squad CLI commands under the hood, creating a WorkflowSyncService to coordinate validation, rendering, and publishing, and adding a `sync-workflow` subcommand to the CLI.

**Tech Stack:** Python 3.12, stdlib (argparse, subprocess, unittest, dataclasses), PyYAML.

---

### Task 1: Core Domain Model Addition

**Files:**
- Modify: `src/core/domain/models.py`
- Test: None (Data class definition only)

- [ ] **Step 1: Define Workflow dataclass in models.py**

Modify [models.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/src/core/domain/models.py) to append the Workflow dataclass:

```python
@dataclass(frozen=True)
class Workflow:
    id: str
    instructions: str
    description: Optional[str] = None
```

- [ ] **Step 2: Commit**

```bash
git add src/core/domain/models.py
git commit -m "domain: add Workflow dataclass"
```

---

### Task 2: Define WorkflowPublisherPort

**Files:**
- Create: `src/core/ports/workflow_publisher.py`
- Test: None (Interface definition only)

- [ ] **Step 1: Create workflow_publisher.py**

Create the file [workflow_publisher.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/src/core/ports/workflow_publisher.py) with the following content:

```python
from abc import ABC, abstractmethod
from src.core.domain.models import Workflow

class WorkflowPublisherPort(ABC):
    @abstractmethod
    def publish(self, workflow: Workflow) -> bool:
        """Publishes a workflow to the external system. Returns True on success."""
        pass
```

- [ ] **Step 2: Commit**

```bash
git add src/core/ports/workflow_publisher.py
git commit -m "ports: define WorkflowPublisherPort interface"
```

---

### Task 3: Implement WorkflowPublisherPort in MulticaAdapter

**Files:**
- Modify: `src/adapters/multica_adapter.py`
- Test: `tests/test_multica_adapter.py`

- [ ] **Step 1: Write the failing tests for squad publishing**

Modify [test_multica_adapter.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/tests/test_multica_adapter.py) to add squad create and update tests. We'll import `Workflow` and add `test_publish_workflow_create_flow` and `test_publish_workflow_update_flow` to the `TestMulticaAdapter` class.

Add the following to the imports in `tests/test_multica_adapter.py`:
```python
from src.core.domain.models import Agent, Workflow
```

Add these tests to `tests/test_multica_adapter.py`:
```python
    @patch("subprocess.run")
    def test_publish_workflow_create_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 1 (squad does not exist)
        mock_get = MagicMock(returncode=1)
        # 2. Mock multica squad create command to return exit code 0 (success)
        mock_create = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_create]
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", description="Manage product features")
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "get", "product-squad"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Verify create command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "create", "--name", "product-squad", "--instructions", "# Product Squad\nDescription...", "--description", "Manage product features"],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_update_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 0 (squad exists)
        mock_get = MagicMock(returncode=0)
        # 2. Mock multica squad update command to return exit code 0 (success)
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update]
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", description="Manage product features")
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "get", "product-squad"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Verify update command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "update", "product-squad", "--instructions", "# Product Squad\nDescription...", "--description", "Manage product features"],
            capture_output=True,
            text=True,
            check=False
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_multica_adapter.py`
Expected: TypeError or signature mismatch

- [ ] **Step 3: Update MulticaAdapter to implement WorkflowPublisherPort and handle Workflows**

Modify [multica_adapter.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/src/adapters/multica_adapter.py):
1. Import `Workflow` and `WorkflowPublisherPort`
2. Update `MulticaAdapter` class definition to inherit from both ports.
3. Update `publish` method to accept `Agent` or `Workflow`, and route to `_publish_agent` or `_publish_workflow`.

```python
from typing import Union
from src.core.domain.models import Agent, Workflow
from src.core.ports.agent_publisher import AgentPublisherPort
from src.core.ports.workflow_publisher import WorkflowPublisherPort

class MulticaAdapter(AgentPublisherPort, WorkflowPublisherPort):
    def __init__(self, runtime_id: str = None):
        self.runtime_id = runtime_id

    def _run_cmd(self, args: list[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False
            )
        except FileNotFoundError:
            res = subprocess.CompletedProcess(args=args, returncode=127)
            res.stderr = "multica: command not found"
            return res

    def publish(self, entity: Union[Agent, Workflow]) -> bool:
        if isinstance(entity, Agent):
            return self._publish_agent(entity)
        elif isinstance(entity, Workflow):
            return self._publish_workflow(entity)
        else:
            raise TypeError(f"Unsupported entity type for publishing: {type(entity)}")

    def _publish_agent(self, agent: Agent) -> bool:
        print(f"Syncing agent {agent.id}...")
        
        check_res = self._run_cmd(["multica", "agent", "get", agent.id])
        
        if check_res.returncode == 0:
            print(f"  Agent '{agent.id}' exists. Updating...")
            cmd = [
                "multica", "agent", "update", agent.id,
                "--instructions", agent.instructions
            ]
            if agent.description:
                cmd += ["--description", agent.description]
        else:
            print(f"  Agent '{agent.id}' not found. Creating...")
            cmd = [
                "multica", "agent", "create",
                "--name", agent.id,
                "--instructions", agent.instructions
            ]
            if self.runtime_id:
                cmd += ["--runtime-id", self.runtime_id]
            if agent.description:
                cmd += ["--description", agent.description]
                
        res = self._run_cmd(cmd)
        if res.returncode != 0:
            print(f"  ✗ Failed to sync '{agent.id}': {res.stderr.strip()}", file=sys.stderr)
            return False
        else:
            print(f"  ✓ Successfully synced '{agent.id}'")
            return True

    def _publish_workflow(self, workflow: Workflow) -> bool:
        print(f"Syncing workflow {workflow.id}...")
        
        check_res = self._run_cmd(["multica", "squad", "get", workflow.id])
        
        if check_res.returncode == 0:
            print(f"  Squad '{workflow.id}' exists. Updating...")
            cmd = [
                "multica", "squad", "update", workflow.id,
                "--instructions", workflow.instructions
            ]
            if workflow.description:
                cmd += ["--description", workflow.description]
        else:
            print(f"  Squad '{workflow.id}' not found. Creating...")
            cmd = [
                "multica", "squad", "create",
                "--name", workflow.id,
                "--instructions", workflow.instructions
            ]
            if workflow.description:
                cmd += ["--description", workflow.description]
                
        res = self._run_cmd(cmd)
        if res.returncode != 0:
            print(f"  ✗ Failed to sync '{workflow.id}': {res.stderr.strip()}", file=sys.stderr)
            return False
        else:
            print(f"  ✓ Successfully synced '{workflow.id}'")
            return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_multica_adapter.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/multica_adapter.py tests/test_multica_adapter.py
git commit -m "adapters: implement WorkflowPublisherPort in MulticaAdapter and add unit tests"
```

---

### Task 4: Implement WorkflowSyncService

**Files:**
- Create: `src/core/services/workflow_sync_service.py`
- Create: `tests/test_workflow_sync_service.py`

- [ ] **Step 1: Create test_workflow_sync_service.py with failing tests**

Create [test_workflow_sync_service.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/tests/test_workflow_sync_service.py):

```python
import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
import yaml

from src.core.services.workflow_sync_service import WorkflowSyncService
from src.core.ports.workflow_publisher import WorkflowPublisherPort
from src.core.domain.models import Workflow

class TestWorkflowSyncService(unittest.TestCase):
    def setUp(self):
        self.publisher = MagicMock(spec=WorkflowPublisherPort)
        self.service = WorkflowSyncService(publisher=self.publisher)
        
        # Valid dummy workflow YAML data
        self.valid_yaml_data = {
            "workflow": {
                "name": "test-workflow",
                "squad_leader": "leader-agent",
                "description": "A test workflow description"
            },
            "agents": [
                {
                    "id": "leader-agent",
                    "role": "Leader",
                    "instructions": "Lead."
                }
            ],
            "steps": []
        }

    def test_sync_workflow_success(self):
        self.publisher.publish.return_value = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_yaml_data, f)
            temp_path = f.name
            
        try:
            success = self.service.sync_workflow(temp_path)
            self.assertTrue(success)
            
            # Verify publisher was called with correct Workflow domain object
            self.publisher.publish.assert_called_once()
            called_workflow = self.publisher.publish.call_args[0][0]
            self.assertIsInstance(called_workflow, Workflow)
            self.assertEqual(called_workflow.id, "test-workflow")
            self.assertEqual(called_workflow.description, "A test workflow description")
            self.assertIn("# Test Workflow", called_workflow.instructions)
        finally:
            os.remove(temp_path)

    def test_sync_workflow_validation_failure(self):
        invalid_yaml_data = {
            "workflow": {
                "name": "" # empty name -> validation error
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_yaml_data, f)
            temp_path = f.name
            
        try:
            success = self.service.sync_workflow(temp_path)
            self.assertFalse(success)
            self.publisher.publish.assert_not_called()
        finally:
            os.remove(temp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_workflow_sync_service.py`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Create the WorkflowSyncService implementation**

Create [workflow_sync_service.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/src/core/services/workflow_sync_service.py):

```python
import yaml
from src.core.ports.workflow_publisher import WorkflowPublisherPort
from src.core.domain.models import Workflow
from src.core.services.workflow_service import validate
from src.adapters.markdown_renderer import render_markdown

class WorkflowSyncService:
    def __init__(self, publisher: WorkflowPublisherPort):
        self.publisher = publisher

    def sync_workflow(self, yaml_path: str) -> bool:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # Validate
        errors = validate(data)
        if errors:
            print(f"Validation failed for {yaml_path}:")
            for e in errors:
                print(f"  ✗ {e}")
            return False

        # Render markdown instructions using yaml_path as canonical relative path
        rendered_md = render_markdown(data, yaml_rel=yaml_path)

        # Construct Workflow domain model
        wf_data = data.get("workflow", {})
        wf_id = wf_data.get("name")
        wf_description = wf_data.get("description")

        workflow = Workflow(
            id=wf_id,
            instructions=rendered_md,
            description=wf_description
        )

        # Publish
        return self.publisher.publish(workflow)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_workflow_sync_service.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/workflow_sync_service.py tests/test_workflow_sync_service.py
git commit -m "services: implement WorkflowSyncService with unit tests"
```

---

### Task 5: Add CLI Subcommand

**Files:**
- Modify: `src/adapters/cli/entrypoint.py`

- [ ] **Step 1: Add cmd_sync_workflow function and parser to entrypoint.py**

Modify [entrypoint.py](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/src/adapters/cli/entrypoint.py):
1. In imports, add `from src.core.services.workflow_sync_service import WorkflowSyncService`
2. Add `cmd_sync_workflow` command handler:
```python
def cmd_sync_workflow(args):
    path = Path(args.yaml)
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    if args.adapter == "multica":
        pub = MulticaAdapter(runtime_id=getattr(args, "runtime_id", None))
    else:
        print(f"Error: Unknown adapter '{args.adapter}'", file=sys.stderr)
        sys.exit(1)

    service = WorkflowSyncService(publisher=pub)
    success = service.sync_workflow(str(path))
    if not success:
        sys.exit(1)
    sys.exit(0)
```
3. Add the subcommand parser in `main()`:
```python
    # sync-workflow
    p_sync_wf = sub.add_parser("sync-workflow", help="validate, render, and sync a workflow YAML to target adapter as a squad")
    p_sync_wf.add_argument("yaml", help="path to workflow YAML")
    p_sync_wf.add_argument("--adapter", default="multica", choices=["multica"], help="target adapter to publish to (default: multica)")
    p_sync_wf.add_argument("--runtime-id", help="runtime ID for the target adapter")
    p_sync_wf.set_defaults(func=cmd_sync_workflow)
```

- [ ] **Step 2: Run the tests to make sure there are no syntax errors or breaking changes**

Run: `python -m unittest discover -s tests`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/adapters/cli/entrypoint.py
git commit -m "cli: add sync-workflow subcommand"
```

---

### Task 6: Add Makefile Integration

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add sync-workflow target to Makefile**

Modify [Makefile](file:///home/huynd/Workspace/pet-projects/agentic-sdlc-system/Makefile):
```makefile
sync-workflow: ## Validate + publish a workflow YAML as a squad to multica (usage: make sync-workflow WORKFLOW=workflow/product-squad.yaml)
	$(PYTHON) -m src.cli sync-workflow $(WORKFLOW) --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))
```

- [ ] **Step 2: Commit**

```bash
git add Makefile
git commit -m "makefile: add sync-workflow target"
```

---

### Task 7: Full Verification

- [ ] **Step 1: Verify all unit tests pass**

Run: `python -m unittest discover -s tests`
Expected: All tests pass successfully.

- [ ] **Step 2: Run dry-run or mock execution via CLI**

Run: `python -m src.cli sync-workflow workflow/orchestrator-debate.yaml`
Expected output:
```
Syncing workflow orchestrator-debate...
  Squad 'orchestrator-debate' not found. Creating...
  ✓ Successfully synced 'orchestrator-debate'
```

- [ ] **Step 3: Run same execution via Makefile**

Run: `make sync-workflow WORKFLOW=workflow/orchestrator-debate.yaml`
Expected output: Same as above.

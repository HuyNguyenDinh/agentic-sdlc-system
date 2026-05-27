# Multica CLI Adapter & Hexagonal Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the existing CLI in `src/` to follow a Hexagonal Architecture (Ports and Adapters) pattern, recursively scan the `agents/` folder for agent Markdown files, and publish/register them directly via the `multica` CLI subprocess.

**Architecture:** Decouple domain models from the filesystem and external platform. We define ports (`AgentRepositoryPort`, `AgentPublisherPort`) and core coordination services, then implement concrete adapters (`FSAgentRepository`, `MulticaAdapter`) and integrate them into the driving CLI.

**Tech Stack:** Python 3, standard libraries (`subprocess`, `argparse`, `pathlib`, `re`, `abc`), `pytest` for testing, `PyYAML` for schema processing.

---

### Task 1: Domain Entities (`src/core/domain/models.py`)

**Files:**
- Create: `src/core/domain/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write unit test for the domain models**
  Create `tests/test_models.py` with standard imports and verification of pure data types:
  ```python
  from src.core.domain.models import Agent

  def test_agent_creation():
      agent = Agent(
          id="pm-agent",
          role="Squad Leader & Orchestrator",
          instructions="Orchestrate everything.",
          description="Project manager agent"
      )
      assert agent.id == "pm-agent"
      assert agent.role == "Squad Leader & Orchestrator"
      assert agent.instructions == "Orchestrate everything."
      assert agent.description == "Project manager agent"
  ```
- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_models.py`
  Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.domain'`
- [ ] **Step 3: Write minimal implementation**
  Create `src/core/domain/models.py`:
  ```python
  from dataclasses import dataclass
  from typing import Optional

  @dataclass(frozen=True)
  class Agent:
      id: str
      role: str
      instructions: str
      description: Optional[str] = None
  ```
- [ ] **Step 4: Run test to verify success**
  Run: `pytest tests/test_models.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add src/core/domain/models.py tests/test_models.py
  git commit -m "feat(domain): define core Agent domain model"
  ```

---

### Task 2: Define Core Ports (`src/core/ports/`)

**Files:**
- Create: `src/core/ports/agent_repository.py`
- Create: `src/core/ports/agent_publisher.py`

- [ ] **Step 1: Create the AgentRepositoryPort interface**
  Create `src/core/ports/agent_repository.py` to establish the abstraction for loading agents:
  ```python
  from abc import ABC, abstractmethod
  from src.core.domain.models import Agent

  class AgentRepositoryPort(ABC):
      @abstractmethod
      def get_all_agents(self) -> list[Agent]:
          """Recursively loads all agents from storage/source."""
          pass
  ```
- [ ] **Step 2: Create the AgentPublisherPort interface**
  Create `src/core/ports/agent_publisher.py` to establish the abstraction for syncing agents:
  ```python
  from abc import ABC, abstractmethod
  from src.core.domain.models import Agent

  class AgentPublisherPort(ABC):
      @abstractmethod
      def publish(self, agent: Agent) -> bool:
          """Registers/updates an agent in the external system. Returns True on success."""
          pass
  ```
- [ ] **Step 3: Commit**
  ```bash
  git add src/core/ports/agent_repository.py src/core/ports/agent_publisher.py
  git commit -m "feat(ports): define ports for agent repository and publisher"
  ```

---

### Task 3: Implement FSAgentRepository Adapter

**Files:**
- Create: `src/adapters/fs_agent_repository.py`
- Test: `tests/test_fs_agent_repository.py`

- [ ] **Step 1: Write test for FSAgentRepository**
  Create `tests/test_fs_agent_repository.py` to verify directory traversal and markdown structure decoding:
  ```python
  import tempfile
  from pathlib import Path
  from src.adapters.fs_agent_repository import FSAgentRepository

  def test_scan_and_parse_agents():
      with tempfile.TemporaryDirectory() as tmp_dir:
          tmp_path = Path(tmp_dir)
          agent_file = tmp_path / "pm-agent.md"
          agent_file.write_text(
              "### **Role**\n"
              "You are the PM Agent.\n"
              "### **Instructions**\n"
              "Follow the workflows strictly."
          )
          
          repo = FSAgentRepository(base_path=tmp_path)
          agents = repo.get_all_agents()
          
          assert len(agents) == 1
          assert agents[0].id == "pm-agent"
          assert agents[0].role == "You are the PM Agent."
          assert "Follow the workflows strictly." in agents[0].instructions
  ```
- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_fs_agent_repository.py`
  Expected: FAIL (ModuleNotFoundError or ImportErrors)
- [ ] **Step 3: Implement FSAgentRepository**
  Create `src/adapters/fs_agent_repository.py`:
  ```python
  import re
  from pathlib import Path
  from src.core.domain.models import Agent
  from src.core.ports.agent_repository import AgentRepositoryPort

  class FSAgentRepository(AgentRepositoryPort):
      def __init__(self, base_path: Path):
          self.base_path = Path(base_path)

      def get_all_agents(self) -> list[Agent]:
          agents = []
          for p in self.base_path.rglob("*.md"):
              if p.name.startswith("."):
                  continue
              content = p.read_text(encoding="utf-8")
              
              role = "Specialist Agent"
              role_match = re.search(r"\*\*Role:\*\*?\s*(.*?)(?:\n|$)", content, re.IGNORECASE)
              if not role_match:
                  role_match = re.search(r"###? \*\*Role\*\*?\s*\n*(.*?)(?:\n|$)", content, re.IGNORECASE)
              
              if role_match:
                  role = role_match.group(1).strip()
              else:
                  title_match = re.search(r"^#\s+(.*?)(?:\n|$)", content)
                  if title_match:
                      role = title_match.group(1).strip()
                  else:
                      role = p.stem.replace("-", " ").title()

              agents.append(
                  Agent(
                      id=p.stem,
                      role=role,
                      instructions=content,
                      description=role
                  )
              )
          return sorted(agents, key=lambda a: a.id)
  ```
- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest tests/test_fs_agent_repository.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add src/adapters/fs_agent_repository.py tests/test_fs_agent_repository.py
  git commit -m "feat(adapters): implement FS agent repository adapter"
  ```

---

### Task 4: Implement MulticaAdapter

**Files:**
- Create: `src/adapters/multica_adapter.py`
- Test: `tests/test_multica_adapter.py`

- [ ] **Step 1: Write Mock test for MulticaAdapter**
  Create `tests/test_multica_adapter.py` to ensure standard get/create/update flows:
  ```python
  from unittest.mock import patch, MagicMock
  from src.adapters.multica_adapter import MulticaAdapter
  from src.core.domain.models import Agent

  @patch("subprocess.run")
  def test_publish_agent_update_flow(mock_run):
      mock_get = MagicMock(returncode=0) # agent exists
      mock_update = MagicMock(returncode=0) # update succeeds
      mock_run.side_effect = [mock_get, mock_update]
      
      adapter = MulticaAdapter()
      agent = Agent(id="coder", role="Coder", instructions="Code.")
      
      assert adapter.publish(agent) is True
      assert mock_run.call_count == 2
  ```
- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_multica_adapter.py`
  Expected: FAIL
- [ ] **Step 3: Implement MulticaAdapter**
  Create `src/adapters/multica_adapter.py`:
  ```python
  import subprocess
  import sys
  from src.core.domain.models import Agent
  from src.core.ports.agent_publisher import AgentPublisherPort

  class MulticaAdapter(AgentPublisherPort):
      def _run_cmd(self, args: list[str]) -> subprocess.CompletedProcess:
          try:
              return subprocess.run(
                  args,
                  capture_output=True,
                  text=True,
                  check=False
              )
          except FileNotFoundError:
              print("Error: multica CLI is not installed or not found on PATH.", file=sys.stderr)
              res = subprocess.CompletedProcess(args=args, returncode=127)
              res.stderr = "multica: command not found"
              return res

      def publish(self, agent: Agent) -> bool:
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
              if agent.description:
                  cmd += ["--description", agent.description]
                  
          res = self._run_cmd(cmd)
          if res.returncode != 0:
              print(f"  ✗ Failed to sync '{agent.id}': {res.stderr.strip()}", file=sys.stderr)
              return False
          else:
              print(f"  ✓ Successfully synced '{agent.id}'")
              return True
  ```
- [ ] **Step 4: Run test to verify success**
  Run: `pytest tests/test_multica_adapter.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add src/adapters/multica_adapter.py tests/test_multica_adapter.py
  git commit -m "feat(adapters): implement multica CLI adapter using subprocess"
  ```

---

### Task 5: Implement Agent Synchronization Service

**Files:**
- Create: `src/core/services/agent_service.py`
- Test: `tests/test_agent_service.py`

- [ ] **Step 1: Write test for AgentService**
  Create `tests/test_agent_service.py`:
  ```python
  from unittest.mock import MagicMock
  from src.core.services.agent_service import AgentService
  from src.core.domain.models import Agent

  def test_sync_all_agents():
      mock_repo = MagicMock()
      mock_repo.get_all_agents.return_value = [
          Agent(id="pm", role="PM", instructions="Sync.")
      ]
      mock_pub = MagicMock()
      mock_pub.publish.return_value = True
      
      service = AgentService(agent_repo=mock_repo, agent_publisher=mock_pub)
      success, failed = service.sync_all_agents()
      
      assert success == 1
      assert failed == 0
  ```
- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_agent_service.py`
  Expected: FAIL
- [ ] **Step 3: Implement AgentService**
  Create `src/core/services/agent_service.py`:
  ```python
  from src.core.ports.agent_repository import AgentRepositoryPort
  from src.core.ports.agent_publisher import AgentPublisherPort

  class AgentService:
      def __init__(self, agent_repo: AgentRepositoryPort, agent_publisher: AgentPublisherPort):
          self.agent_repo = agent_repo
          self.agent_publisher = agent_publisher

      def sync_all_agents(self) -> tuple[int, int]:
          agents = self.agent_repo.get_all_agents()
          print(f"Found {len(agents)} agents locally. Starting synchronization...")
          
          success_count = 0
          fail_count = 0
          
          for agent in agents:
              if self.agent_publisher.publish(agent):
                  success_count += 1
              else:
                  fail_count += 1
                  
          print(f"\nDone. Synced: {success_count}, Failed: {fail_count}")
          return success_count, fail_count
  ```
- [ ] **Step 4: Run test to verify success**
  Run: `pytest tests/test_agent_service.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add src/core/services/agent_service.py tests/test_agent_service.py
  git commit -m "feat(services): implement core AgentService sync flow"
  ```

---

### Task 6: Refactor Legacy Code and Workflows

**Files:**
- Create: `src/adapters/markdown_renderer.py`
- Create: `src/core/services/workflow_service.py`

- [ ] **Step 1: Move rendering and schema logic**
  Port legacy code from `src/render.py` into `src/adapters/markdown_renderer.py`, and legacy code from `src/schema.py` into `src/core/services/workflow_service.py`. Keep standard validator helper `validate` signature.
- [ ] **Step 2: Verify existing validation tests pass**
  Run: `python3 -m src.test_schema`
  Expected: PASS
- [ ] **Step 3: Commit**
  ```bash
  git add src/adapters/markdown_renderer.py src/core/services/workflow_service.py
  git commit -m "refactor(core): migrate legacy rendering and validation into hexagonal package structure"
  ```

---

### Task 7: CLI Driving Adapter Integration

**Files:**
- Create: `src/adapters/cli/entrypoint.py`
- Modify: `src/cli.py`

- [ ] **Step 1: Implement driving CLI parser**
  Create `src/adapters/cli/entrypoint.py` with support for legacy commands plus new `sync-agents` subcommand:
  ```python
  import argparse
  import sys
  from pathlib import Path
  import yaml

  from src.core.services.agent_service import AgentService
  from src.adapters.fs_agent_repository import FSAgentRepository
  from src.adapters.multica_adapter import MulticaAdapter
  from src.core.services.workflow_service import validate, EXAMPLE_WORKFLOW
  from src.adapters.markdown_renderer import render_file

  def cmd_create(args):
      path = Path(args.name)
      if not path.suffix:
          path = path.with_suffix(".yaml")
      if path.exists():
          print(f"Error: {path} already exists. Use --force to overwrite.")
          sys.exit(1)
      content = yaml.dump(EXAMPLE_WORKFLOW, default_flow_style=False, sort_keys=False, allow_unicode=True)
      base = Path(args.name).stem
      content = content.replace("name: example-workflow", f"name: {base}")
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(content)
      print(f"Created: {path}")

  def cmd_validate(args):
      path = Path(args.yaml)
      if not path.exists():
          print(f"Error: {path} not found")
          sys.exit(1)
      with open(path) as f:
          data = yaml.safe_load(f)
      errors = validate(data)
      if errors:
          print(f"Validation failed for {path}:")
          for e in errors:
              print(f"  ✗ {e}")
          sys.exit(1)
      else:
          print(f"✓ {path} is valid")

  def cmd_apply(args):
      path = Path(args.yaml)
      if not path.exists():
          print(f"Error: {path} not found")
          sys.exit(1)
      with open(path) as f:
          data = yaml.safe_load(f)
      errors = validate(data)
      if errors:
          print(f"Validation failed — cannot apply:")
          for e in errors:
              print(f"  ✗ {e}")
          sys.exit(1)
      output = args.output
      if not output:
          output = path.with_suffix(".md")
      render_file(str(path), str(output))
      print(f"Applied: {path} → {output}")

  def cmd_sync_agents(args):
      project_root = Path(__file__).resolve().parent.parent.parent.parent
      agents_dir = project_root / "agents"
      
      repo = FSAgentRepository(base_path=agents_dir)
      pub = MulticaAdapter()
      service = AgentService(agent_repo=repo, agent_publisher=pub)
      
      success, failed = service.sync_all_agents()
      if failed > 0:
          sys.exit(1)
      sys.exit(0)

  def main():
      parser = argparse.ArgumentParser(
          description="agentic-sdlc — Hexagonal IaC CLI for SDLC workflows"
      )
      sub = parser.add_subparsers(dest="command", required=True)

      # create
      p_create = sub.add_parser("create", help="scaffold a new workflow YAML")
      p_create.add_argument("name", help="workflow name")
      p_create.set_defaults(func=cmd_create)

      # validate
      p_validate = sub.add_parser("validate", help="validate a workflow YAML against schema")
      p_validate.add_argument("yaml", help="path to workflow YAML")
      p_validate.set_defaults(func=cmd_validate)

      # apply
      p_apply = sub.add_parser("apply", help="validate + render workflow YAML to markdown")
      p_apply.add_argument("yaml", help="path to workflow YAML")
      p_apply.add_argument("-o", "--output", help="output markdown path")
      p_apply.set_defaults(func=cmd_apply)

      # sync-agents
      p_sync = sub.add_parser("sync-agents", help="scan agents directory recursively and publish to Multica")
      p_sync.set_defaults(func=cmd_sync_agents)

      args = parser.parse_args()
      args.func(args)
  ```
- [ ] **Step 2: Modify legacy thin CLI script**
  Modify `src/cli.py` to act as a thin driving wrapper pointing directly to the entrypoint:
  ```python
  #!/usr/bin/env python3
  """IaC CLI entry point delegating to Hexagonal adapters."""
  from src.adapters.cli.entrypoint import main

  if __name__ == "__main__":
      main()
  ```
- [ ] **Step 3: Run validation check**
  Run: `python3 -m src.cli --help`
  Expected: Prints the newly unified subcommands help including `sync-agents`.
- [ ] **Step 4: Commit**
  ```bash
  git add src/adapters/cli/entrypoint.py src/cli.py
  git commit -m "feat(cli): bind Multica sync integration into standard IaC subcommands"
  ```

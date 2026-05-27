# Support runtime-id in Multica Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable passing and propagating a `--runtime-id` parameter from the Makefile and Python CLI to the `multica` output adapter to successfully sync/create agents.

**Architecture:** Extend the CLI arg parser `sync-agent` command to accept `--runtime-id`, propagate this parameter to the `MulticaAdapter` instance constructor, and conditionally append `--runtime-id <value>` during subprocess execution of `multica agent create`.

**Tech Stack:** Python 3 (unittest, subprocess, argparse), GNU Make.

---

### Task 1: Update CLI Argument Parser

**Files:**
- Modify: `src/adapters/cli/entrypoint.py`

- [ ] **Step 1: Update `cmd_sync_agent` to pass `runtime_id` to `MulticaAdapter`**
  Modify `cmd_sync_agent` to extract `runtime_id` from parsed arguments and supply it to the constructor of `MulticaAdapter`:
  ```python
  def cmd_sync_agent(args):
      # Determine agents directory relative to project root
      project_root = Path(__file__).resolve().parent.parent.parent.parent
      agents_dir = project_root / "agents"
      
      repo = FSAgentRepository(base_path=agents_dir)
      
      if args.adapter == "multica":
          pub = MulticaAdapter(runtime_id=getattr(args, "runtime_id", None))
      else:
          print(f"Error: Unknown adapter '{args.adapter}'", file=sys.stderr)
          sys.exit(1)
          
      service = AgentService(agent_repo=repo, agent_publisher=pub)
      
      success, failed = service.sync_all_agents()
      if failed > 0:
          sys.exit(1)
      sys.exit(0)
  ```

- [ ] **Step 2: Add `--runtime-id` argument to the `sync-agent` command subparser**
  Modify `main` inside `entrypoint.py` to add `--runtime-id`:
  ```python
      # sync-agent
      p_sync = sub.add_parser("sync-agent", help="scan agents directory recursively and publish to target adapter")
      p_sync.add_argument("--adapter", default="multica", choices=["multica"], help="target adapter to publish to (default: multica)")
      p_sync.add_argument("--runtime-id", help="runtime ID for the multica adapter")
      p_sync.set_defaults(func=cmd_sync_agent)
  ```

- [ ] **Step 3: Run existing unit tests to verify no syntax errors or regressions**
  Run: `pyenv local 3.12.12 && python -m unittest discover -s tests`
  Expected: PASS

- [ ] **Step 4: Commit CLI parser changes**
  ```bash
  git add src/adapters/cli/entrypoint.py
  git commit -m "feat(cli): add --runtime-id option to sync-agent command"
  ```

---

### Task 2: Implement `runtime_id` Propagations in `MulticaAdapter`

**Files:**
- Modify: `src/adapters/multica_adapter.py`

- [ ] **Step 1: Add `runtime_id` to `MulticaAdapter` constructor**
  Update the `__init__` constructor of `MulticaAdapter` to accept `runtime_id` with a default value of `None`:
  ```python
  class MulticaAdapter(AgentPublisherPort):
      def __init__(self, runtime_id: str = None):
          self.runtime_id = runtime_id
  ```

- [ ] **Step 2: Update `publish` to append `--runtime-id` in the `create` command flow**
  Modify the `publish` method so that when a new agent is created, `--runtime-id` is conditionally added if `self.runtime_id` is specified:
  ```python
          else:
              # Agent does not exist, perform create
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
  ```

- [ ] **Step 3: Commit adapter changes**
  ```bash
  git add src/adapters/multica_adapter.py
  git commit -m "feat(adapter): support passing --runtime-id during agent creation"
  ```

---

### Task 3: Add and Update Unit Tests

**Files:**
- Modify: `tests/test_multica_adapter.py`

- [ ] **Step 1: Add a test case for `publish` with a `runtime_id`**
  Append `test_publish_agent_create_flow_with_runtime_id` inside the `TestMulticaAdapter` class in `tests/test_multica_adapter.py`:
  ```python
      @patch("subprocess.run")
      def test_publish_agent_create_flow_with_runtime_id(self, mock_run):
          # 1. Mock multica get command to return exit code 1 (agent does not exist)
          mock_get = MagicMock(returncode=1)
          # 2. Mock multica create command to return exit code 0 (success)
          mock_create = MagicMock(returncode=0)
          mock_run.side_effect = [mock_get, mock_create]
          
          adapter = MulticaAdapter(runtime_id="my-test-runtime")
          agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")
          
          success = adapter.publish(agent)
          
          self.assertTrue(success)
          self.assertEqual(mock_run.call_count, 2)
          
          # Verify get command arguments
          mock_run.assert_any_call(
              ["multica", "agent", "get", "coder"],
              capture_output=True,
              text=True,
              check=False
          )
          
          # Verify create command arguments contains --runtime-id
          mock_run.assert_any_call(
              ["multica", "agent", "create", "--name", "coder", "--instructions", "Code.", "--runtime-id", "my-test-runtime", "--description", "Coder"],
              capture_output=True,
              text=True,
              check=False
          )
  ```

- [ ] **Step 2: Run all unit tests to ensure they all pass**
  Run: `pyenv local 3.12.12 && python -m unittest discover -s tests`
  Expected: PASS

- [ ] **Step 3: Commit test updates**
  ```bash
  git add tests/test_multica_adapter.py
  git commit -m "test(adapter): add unit test for multica sync with runtime-id"
  ```

---

### Task 4: Integrate in Makefile

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Define RUNTIME_ID variable and update sync-agent command**
  Modify `Makefile` to accept `RUNTIME_ID ?=` and forward it:
  ```makefile
  WORKFLOW ?= workflow/orchestrator-debate.yaml
  ADAPTER ?= multica
  RUNTIME_ID ?=
  ```
  And update the `sync-agent` target:
  ```makefile
  sync-agent: ## Scan agents directory recursively and publish to target adapter (usage: make sync-agent ADAPTER=multica RUNTIME_ID=my-id)
  	$(PYTHON) -m src.cli sync-agent --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))
  ```

- [ ] **Step 2: Verify CLI invocation works through Make (dry run via unit test/dry command if possible)**
  Run the test suite through make:
  Run: `make test`
  Expected: PASS

- [ ] **Step 3: Commit Makefile updates**
  ```bash
  git add Makefile
  git commit -m "feat(make): support RUNTIME_ID parameter in sync-agent target"
  ```

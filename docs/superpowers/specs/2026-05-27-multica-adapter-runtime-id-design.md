# Design Specification: Support runtime-id in Multica Adapter

This document outlines the design for adding `--runtime-id` parameter support in the `multica` adapter, propagating it from the Makefile and Python CLI to the underlying `multica` CLI subprocess calls.

## Background and Goals

When using the `multica` CLI to register/create new agents, a `--runtime-id` is required. The current adapter fails to supply this argument, resulting in errors like:
```text
  Agent 'sa-agent' not found. Creating...
  ✗ Failed to sync 'sa-agent': Error: --runtime-id is required
```

The goals are:
1. **Extend CLI**: Update the `agentic-sdlc` Python CLI `sync-agent` command to accept an optional `--runtime-id` argument.
2. **Propagate to Adapter**: Modify `MulticaAdapter` to accept a `runtime_id` parameter and include `--runtime-id <value>` when invoking `multica agent create`.
3. **Makefile Integration**: Allow passing `RUNTIME_ID` as a Make variable (e.g., `make sync-agent RUNTIME_ID=my-runtime-id`) and conditionally forward it to the CLI.

---

## Proposed Changes

### 1. `Makefile`
Update the `sync-agent` target to conditionally forward `--runtime-id` if defined:
```makefile
sync-agent: ## Scan agents directory recursively and publish to target adapter (usage: make sync-agent ADAPTER=multica RUNTIME_ID=my-id)
	$(PYTHON) -m src.cli sync-agent --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))
```

### 2. `src/adapters/cli/entrypoint.py`
Add the `--runtime-id` parser argument and forward it to `MulticaAdapter`:
```python
def cmd_sync_agent(args):
    ...
    if args.adapter == "multica":
        pub = MulticaAdapter(runtime_id=getattr(args, "runtime_id", None))
    ...
```

### 3. `src/adapters/multica_adapter.py`
Introduce `runtime_id` to the constructor and append it to the command list when creating an agent:
```python
class MulticaAdapter(AgentPublisherPort):
    def __init__(self, runtime_id: str = None):
        self.runtime_id = runtime_id

    # In publish:
    ...
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

---

## Verification Plan

### Automated Tests
1. **`tests/test_multica_adapter.py`**:
   - Verify `MulticaAdapter` without `runtime_id` functions normally and does not append `--runtime-id` (backwards compatibility).
   - Verify `MulticaAdapter` with `runtime_id` correctly appends `"--runtime-id"` and its value to the `multica agent create` arguments.
2. Run the test suite:
   ```bash
   pyenv local 3.12.12 && python -m unittest discover -s tests
   ```

### Manual Verification
1. Run `make sync-agent ADAPTER=multica RUNTIME_ID=test-id` and check that the correct subprocess commands are formulated.

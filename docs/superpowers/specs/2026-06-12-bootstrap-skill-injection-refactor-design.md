---
description: Refactor bootstrap skill installation and Multica skill injection so local install, Multica import, baseline assignment, and per-agent IaC bindings work through one coherent flow
---

# Bootstrap Skill Injection Refactor Design

## Problem

The current bootstrap flow does not present skill setup as a coherent installation path. The Python CLI has a `bootstrap-skills` command, but the Makefile does not expose it. The umbrella `bootstrap` command installs skills from `skills.txt`, syncs agents and workflows, and then imports skills into Multica, which makes skill availability and agent assignment feel bolted on after the agent sync.

The Multica adapter also ignores the `agent.skills` field already present in the Agent IaC schema. This means agent-specific skill declarations cannot be injected when agents are published to Multica.

## Goals

- Expose Multica skill bootstrap through the installation CLI and Makefile.
- Keep local skill installation from `skills.txt` separate from Multica skill import and assignment.
- Import baseline skills into Multica before agents are synced.
- Support hybrid skill assignment:
  - baseline skills can still be assigned to all agents for compatibility;
  - per-agent IaC `skills` declarations are applied when each agent is published.
- Make bootstrap ordering explicit and testable.
- Preserve dry-run behavior across install, import, sync, and assignment steps.

## Non-Goals

- Do not change the external `npx skills add` behavior for local installation.
- Do not replace existing agent or workflow schemas.
- Do not remove global baseline assignment yet; keep it as a compatibility fallback.
- Do not make normal agent publishing install skills from remote registries.

## Recommended Approach

Use a hybrid bootstrap service.

Create a shared Multica skill service that owns skill discovery, Multica skill create/update, ID resolution, agent listing, and agent skill assignment. The existing `src.bootstrap_multica_skills` module becomes a thin CLI wrapper around that service.

`src.install_skills` remains responsible only for local installation from `skills.txt`.

`MulticaAdapter` receives optional skill-binding support. When publishing an agent, the adapter reads `agent.iac_schema["agent"]["skills"]` when present, resolves those skill names through the shared service, and assigns the resolved skill IDs to the published agent after create/update succeeds.

## Bootstrap Flow

The umbrella `bootstrap` command should run these steps in order:

1. Bootstrap the Obsidian Wiki runtime.
2. Install local skills from `skills.txt` through the installation CLI behavior.
3. Import baseline skills into Multica.
4. Sync agents to Multica, applying per-agent IaC skill bindings after each agent create/update.
5. Sync the workflow to Multica.
6. Assign baseline skills to all agents as the compatibility fallback.

This ordering makes skills available before agent sync, lets agent-specific bindings happen inside the Multica adapter, and keeps the existing broad baseline assignment for agents that do not yet declare skills.

## Components

### Local Skill Installer

`src.install_skills` continues to parse `skills.txt` and run `npx skills add ... -y -g`. It should remain independent of Multica and should not know about agent assignment.

### Multica Skill Service

The shared service should provide a small API:

- scan local skill directories for `SKILL.md`;
- filter to the baseline skill set;
- create or update skills in Multica;
- resolve skill names to Multica skill IDs;
- list Multica agents;
- assign a set of skill IDs to one agent or all agents;
- support dry-run output without mutation commands.

The service may initially reuse the existing parsing and subprocess logic from `src.bootstrap_multica_skills`, but the public functions should be organized around these responsibilities instead of one script-shaped flow.

### Multica Bootstrap Wrapper

`src.bootstrap_multica_skills` should become the CLI-facing wrapper. It should parse arguments, call the service to import baseline skills, and optionally assign them to all agents.

The existing `bootstrap-skills` Python CLI command should continue to exist. The Makefile should expose it with a `bootstrap-skills` target so users can run just the Multica import and assignment step.

### Multica Adapter

`MulticaAdapter` should accept an optional skill service. If an agent has IaC skill declarations, the adapter should:

1. publish the agent as it does today;
2. resolve the published agent UUID;
3. resolve declared skill names to IDs;
4. assign those skill IDs to that agent.

If an agent has no declared skills, the adapter should skip per-agent assignment. Baseline assignment remains owned by bootstrap, not by normal `sync-agent`.

## Error Handling

Skill installation from `skills.txt` and Multica baseline import should be hard failures in `bootstrap`, because later steps depend on installed and importable skills.

If an agent explicitly declares IaC skills, unresolved skills or assignment failures should make that agent publish fail. Silent partial skill injection would make the agent state misleading.

Baseline assignment to all agents should report per-agent failures and make `bootstrap` fail if any assignment fails.

Dry-run should not execute `npx` or mutating `multica` commands. It should print the intended order and the planned skill imports and assignments.

## Testing

Add or update tests for:

- CLI wiring for `bootstrap-skills`;
- Makefile target visibility for `bootstrap-skills`;
- umbrella `bootstrap` calls steps in the intended order;
- Multica skill service create/update/resolve/assign behavior;
- dry-run behavior for skill import and assignment;
- `MulticaAdapter` assigns IaC-declared skills after agent create/update;
- explicit missing or unassignable IaC skills cause agent publish failure;
- existing agent and workflow publishing behavior remains unchanged when no skills are declared.

## Acceptance Criteria

- `make help` shows a `bootstrap-skills` target.
- `python -m src.cli bootstrap-skills --dry-run` works without mutating Multica.
- `python -m src.cli bootstrap --dry-run` prints skill installation, Multica skill import, agent sync, workflow sync, and baseline assignment in the intended order.
- Agents with IaC `skills` declarations receive those specific skills during Multica publication.
- Agents without IaC `skills` declarations continue to rely on baseline assignment during bootstrap.
- Unit tests cover the new flow and existing tests remain green.

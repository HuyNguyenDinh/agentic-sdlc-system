---
description: Define a centralized skills catalog with component-scoped registries and per-agent sidecar files that explicitly pull skills — replacing global baseline assignment with precise, intentional skill injection
---

# Skills Module & Sidecar Injection Design

## Problem

All agents currently receive the same global set of skills via a bulk bootstrap assignment. There is no mechanism to give each agent only the skills relevant to its role. This causes skill overload: agents are loaded with skills they will never use, making skill selection noisier and harder to reason about.

The IaC schema already has a `skills:` field on agents, but it is a flat list of names and is ignored by the Multica adapter. The `skills.txt` file is a flat list of GitHub URLs with no component grouping or agent-level mapping.

## Goals

- Replace `skills.txt` with a structured central YAML catalog.
- Organize skills by agent component (solution_architect, coding, qa, product, management, devops, shared).
- Give each agent a sidecar `.skills.yaml` file that explicitly declares which component skill sets to pull.
- Remove global "assign all skills to all agents" bootstrap behavior entirely.
- Every skill assignment is intentional — no implicit injection.

## Non-Goals

- Do not change the `npx skills add` local installation behavior.
- Do not remove or alter the `.iac.yaml` schema — the deprecated `skills:` field is left in place but ignored once sidecars exist.
- Do not auto-merge `shared` skills into agents — agents must explicitly pull them.

## Directory Structure

Remove all existing content from `skills/` (directories, submodule references, symlinks) before setting up the new structure.

```
skills/
  skills.yaml                          # root catalog — imports all component registries
  components/
    solution_architect/
      skills.yaml
    coding/
      skills.yaml
    qa/
      skills.yaml
    product/
      skills.yaml
    management/
      skills.yaml
    devops/
      skills.yaml
    shared/
      skills.yaml                      # minimal cross-cutting skills; explicit pull only

agents/
  solution_architect/
    sa-agent.iac.yaml                  # unchanged
    sa-agent.skills.yaml               # NEW sidecar
    sa-critic-agent.iac.yaml
    sa-critic-agent.skills.yaml
  coding/
    coder-agent.skills.yaml
    ...
  qa/
    qa-agent.skills.yaml
    ...
  product/
    product-manager-agent.skills.yaml
    ...
```

## File Schemas

### `skills/skills.yaml` — root catalog

```yaml
version: 1

imports:
  - skills/components/solution_architect
  - skills/components/coding
  - skills/components/qa
  - skills/components/product
  - skills/components/management
  - skills/components/devops
  - skills/components/shared
```

### `skills/components/{component}/skills.yaml` — component registry

```yaml
version: 1
component: solution_architect

repos:
  - name: architecture-skills
    url: https://github.com/org/architecture-skills
    skills:
      - architecture-design
      - technical-review
      - risk-assessment
      - dependency-analysis
  - name: superpowers
    url: https://github.com/org/superpowers
    skills:
      - brainstorming
      - writing-plans
```

### `agents/{component}/{agent}.skills.yaml` — agent sidecar

```yaml
version: 1
agent: sa-agent

pull:
  - skills/components/solution_architect
  - skills/components/shared

override:
  include: [brainstorming]
  exclude: [risk-assessment]
```

- `pull` — list of component paths to import from (resolved against project root)
- `override.include` — skill names to add on top of pulled sets
- `override.exclude` — skill names to remove from pulled sets
- Agents with no sidecar file receive no skills assigned

## Python Services

### `src/core/services/skills_catalog_service.py`

Reads `skills/skills.yaml`, resolves each import path to its component file, and merges into a unified catalog.

```python
class SkillsCatalogService:
    def get_install_urls(self) -> List[str]: ...
    def get_component_skills(self, component: str) -> List[str]: ...
    def get_all_skills(self) -> Dict[str, List[str]]: ...
```

- `get_install_urls()` — all repo URLs across all components; replaces `skills.txt` reader in `install_skills.py`
- `get_component_skills(component)` — skill names for a given component name
- `get_all_skills()` — full component → skills map

### `src/core/services/skills_sidecar_service.py`

Reads an agent's `.skills.yaml` sidecar, resolves each `pull:` path through the catalog, and applies `override.include` / `override.exclude`.

```python
class SkillsSidecarService:
    def get_skills_for_agent(self, agent_id: str) -> List[str]: ...
    def has_sidecar(self, agent_id: str) -> bool: ...
```

- `get_skills_for_agent(agent_id)` — final resolved skill list; raises if sidecar references an unknown component
- `has_sidecar(agent_id)` — returns False if no sidecar file exists for that agent

## Integration Changes

| File | Change |
|---|---|
| `src/install_skills.py` | Replace `skills.txt` reader with `SkillsCatalogService.get_install_urls()` |
| `src/adapters/multica_adapter.py` | After agent create/update, call `SkillsSidecarService.get_skills_for_agent()` and assign resolved skills; skip if `has_sidecar()` is False |
| `src/bootstrap_multica_skills.py` | Remove global "assign all to all" step; bootstrap only imports skills into Multica (create/update), not assignment |

## Bootstrap Flow

1. Bootstrap Obsidian Wiki runtime.
2. Install local skills from catalog via `install_skills.py` (reads `SkillsCatalogService.get_install_urls()`).
3. Import all skills into Multica (create/update via `bootstrap_multica_skills.py`).
4. Sync agents to Multica — adapter assigns sidecar-declared skills per agent after each create/update.
5. Sync workflows to Multica.

No global baseline assignment step. Agents without sidecars receive no skills.

## Error Handling

- Unknown component in a sidecar `pull:` path → agent publish fails with a clear error naming the path.
- Skill name in `override.include` or `override.exclude` that does not exist in any pulled component → fail with the unknown skill name.
- Missing sidecar → skip assignment silently (agent gets no skills; logged at info level).
- Dry-run → print resolved skill assignments per agent without mutating Multica.

## Migration

1. Remove all existing content from `skills/` (directories, submodule entries, symlinks).
2. Create `skills/components/` structure and populate component `skills.yaml` files from the existing `skills.txt` URLs.
3. Create `.skills.yaml` sidecars for all existing agents, mapping their current IaC `skills:` lists to component pulls.
4. Update `install_skills.py`, `multica_adapter.py`, `bootstrap_multica_skills.py`.
5. Remove the deprecated `skills:` field from all `.iac.yaml` files once sidecars are in place.

## Testing

- `SkillsCatalogService` resolves imports and builds correct component → skills map.
- `SkillsSidecarService` resolves pulls, applies include/exclude, raises on unknown component or skill.
- `MulticaAdapter` assigns sidecar skills after agent create/update; skips agents without sidecars.
- `bootstrap_multica_skills.py` no longer assigns skills globally.
- `install_skills.py` reads URLs from catalog, not `skills.txt`.
- Dry-run prints assignments without mutating Multica.
- Agents without sidecars publish successfully with no skill assignment.

## Acceptance Criteria

- `skills/` contains only `skills.yaml` and `components/` — no old dirs, submodules, or symlinks.
- Every agent in `agents/` has a `.skills.yaml` sidecar.
- `python -m src.cli bootstrap --dry-run` prints per-agent skill assignments from sidecars.
- Agents with sidecars receive exactly the declared skills after bootstrap.
- Agents without sidecars receive no skills.
- No `skills.txt` references remain in Python source.

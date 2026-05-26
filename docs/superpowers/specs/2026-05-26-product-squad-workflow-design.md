# Product Squad Workflow & Knowledge Sources Schema Extension

## Overview

Two deliverables in one spec:

1. **Schema extension**: Add a `knowledge_sources` top-level section to workflow YAML, defining what knowledge bases each squad has access to. The rendered markdown must include explicit KB interaction protocols — agents query KB before work, update KB after work.
2. **Product squad workflow**: A new workflow YAML (`product-squad.yaml`) for the product squad, following the same structural patterns as the development squad's `orchestrator-debate.yaml`.

## Design Decisions

- **KB interaction is an agent-level concern**, not a workflow step — agents discover tools via the skills system (e.g., `wiki-query`, `wiki-ingest` from obsidian-wiki).
- **`knowledge_sources` is declarative** — it says _what_ is available, not _how_ to use it. Agent `.md` definitions specify the how.
- **The rendered markdown must include KB protocol instructions** — the `render.py` output explicitly tells agents to read KB before work and write KB after work, based on access levels.
- **Product squad workflow is self-contained** — no chaining to the development squad. The approved PRD is the handoff artifact.
- **Minimal agent roster** — Product Lead (orchestrator) + Product Manager (writer) + Product Critic (reviewer).

---

## Schema: `knowledge_sources`

### YAML structure

```yaml
knowledge_sources:
  - id: llm-wiki             # unique identifier, kebab-case
    type: wiki                # wiki | repository | external
    description: >            # human-readable description
      Obsidian-based organizational knowledge base
    access: [read, write]     # subset of [read, write]
```

### Valid types

| Type | Description | Example |
|------|-------------|---------|
| `wiki` | LLM-WIKI / Obsidian knowledge base | Organizational wiki |
| `repository` | Source code repository | Project codebase |
| `external` | External data source | Customer feedback, analytics |

### JSON Schema addition (in `src/schema.py`)

Add to `JSON_SCHEMA["properties"]`:

```python
"knowledge_sources": {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "type", "description", "access"],
        "properties": {
            "id": {"type": "string", "pattern": ID_PATTERN},
            "type": {"enum": ["wiki", "repository", "external"]},
            "description": {"type": "string"},
            "access": {
                "type": "array",
                "items": {"enum": ["read", "write"]},
                "minItems": 1,
                "uniqueItems": True,
            },
        },
    },
}
```

### Validation rules (in `validate()`)

- `knowledge_sources` is optional (not added to top-level `required`)
- If present, must be a list
- Each item must have `id`, `type`, `description`, `access`
- `id` must be unique across all knowledge sources
- `type` must be one of: `wiki`, `repository`, `external`
- `access` must be a non-empty array containing only `read` and/or `write`

---

## Rendered Markdown: KB Protocol

### Knowledge Sources table

Rendered between the Agents table and the Workflow diagram:

```markdown
## Knowledge Sources

| Source | Type | Description | Access |
|--------|------|-------------|--------|
| `llm-wiki` | wiki | Obsidian-based organizational knowledge base | read, write |
| `customer-feedback` | external | Customer feedback, support tickets, and usage analytics | read |

### Knowledge Base Protocol

All agents in this squad **MUST** follow these knowledge base interaction rules:

**Before starting work** — query these sources to discover relevant prior art, decisions, patterns, and context. Use findings to inform and ground your work in existing organizational knowledge:
- `llm-wiki` (wiki)
- `customer-feedback` (external)

**After completing work** — update these sources with new artifacts, decisions, and learnings. Maintain and enrich the knowledge base at your responsibility layer level. Ensure exported knowledge is structured, cross-referenced, and reusable by other squads:
- `llm-wiki` (wiki)
```

The protocol section is only rendered when `knowledge_sources` is present and non-empty. "Before starting work" lists sources with `read` in their `access` array. "After completing work" lists sources with `write` in their `access` array. Each source is rendered as `` `{id}` ({type}) ``.

---

## Product Squad Workflow YAML

File: `workflow/product-squad.yaml`

### Agents

| Agent | Role | Path |
|-------|------|------|
| `product-lead-agent` | Squad Leader & Orchestrator | `agents/product/product-lead.md` |
| `product-manager-agent` | Product Manager & PRD Writer | `agents/product/product-manager.md` |
| `product-critic-agent` | Product Critic & Reviewer | `agents/product/product-critic.md` |

### Knowledge Sources

| Source | Type | Access |
|--------|------|--------|
| `llm-wiki` | wiki | read, write |
| `customer-feedback` | external | read |

### Steps

| # | ID | Type | Description | Actor | Transitions |
|---|-----|------|-------------|-------|-------------|
| 1 | `discovery` | delegate | PM drafts discovery brief from raw feature request | `product-manager-agent` | → 2 |
| 2 | `discovery-debate` | debate | PM and Critic debate the discovery brief (max 3) | PM ↔ Critic | approved/max → 3 |
| 3 | `discovery-review` | hitl | Stakeholder reviews discovery brief | — | approved → 4, rejected → 1 |
| 4 | `prd-drafting` | delegate | PM writes detailed PRD from approved brief | `product-manager-agent` | → 5 |
| 5 | `prd-debate` | debate | PM and Critic debate the PRD (max 3) | PM ↔ Critic | approved/max → 6 |
| 6 | `prd-review` | hitl | Stakeholder reviews the final PRD | — | approved → 7, rejected → 4 |
| 7 | `packaging` | delegate | Product Lead packages approved PRD and exports to KB | `product-lead-agent` | → Done |

---

## Development Squad YAML Update

Add `knowledge_sources` to existing `workflow/orchestrator-debate.yaml`:

```yaml
knowledge_sources:
  - id: codebase
    type: repository
    description: Project source code and documentation
    access: [read, write]

  - id: llm-wiki
    type: wiki
    description: Obsidian-based organizational knowledge base
    access: [read, write]
```

No other changes to the development squad workflow.

---

## Agent Definitions

### `agents/product/product-lead.md`

**Role:** Squad Leader & Orchestrator for the Product Squad.

**Responsibilities:**
- Route workflows between PM and Critic agents
- Manage debate cycles with `{MAX_TURN}` enforcement
- Trigger HITL approval gates for stakeholder review
- Package final approved PRD for handoff to development squad
- Export approved artifacts to LLM-WIKI knowledge base

**KB interaction:**
- Before orchestrating: query LLM-WIKI for organizational strategy, past product decisions, and related PRDs
- After approval gates: export approved discovery briefs and PRDs to LLM-WIKI
- Maintain cross-references between new artifacts and existing knowledge

**Constraints:**
- Centralized communication — all agent communication flows through this agent
- Strict `{MAX_TURN}` enforcement at every debate stage
- Does not write PRDs or perform reviews directly

### `agents/product/product-manager.md`

**Role:** Product Manager & PRD Writer.

**Responsibilities:**
- Phase 1 (Discovery): Analyze raw feature requests, synthesize market context, user needs, and constraints into a discovery brief
- Phase 2 (PRD): Transform approved discovery brief into a detailed PRD following the PRD skill schema (Executive Summary, User Experience, Technical Specs, Risks & Roadmap)
- Respond to critic feedback with evidence-based revisions or reasoned defenses

**KB interaction:**
- Before drafting: query LLM-WIKI for prior art, related features, past decisions, patterns
- Before drafting: query customer feedback sources for relevant user data, support tickets, usage patterns
- Use KB findings to ground requirements in real data, not assumptions

**Quality standards:**
- Concrete, measurable requirements (no "fast", "easy", "intuitive")
- User stories in `As a [user], I want to [action] so that [benefit]` format
- Acceptance criteria with "Done" definitions for each story
- Non-goals explicitly defined to protect scope

### `agents/product/product-critic.md`

**Role:** Product Critic & Adversarial Reviewer.

**Responsibilities:**
- Challenge discovery briefs for assumption gaps, missing market context, weak user evidence
- Challenge PRDs for vague requirements, missing edge cases, scope creep, feasibility risks
- Validate claims against knowledge base evidence

**KB interaction:**
- Before reviewing: query LLM-WIKI for contradicting evidence, past failures, related decisions
- Before reviewing: query customer feedback for data that supports or contradicts the PM's claims
- Use KB evidence to strengthen critiques — not just opinions, but data-backed challenges

**Review lenses:**
1. Requirements Quality — flag vague, unmeasurable, or untestable requirements
2. User Evidence — demand data-backed user needs, not assumed personas
3. Scope Discipline — identify scope creep, features without clear user value
4. Feasibility — flag technical risks the PM may have missed
5. Consistency — find contradictions between sections

**Output constraints:**
- SUCCESS signal if the artifact is comprehensive, evidence-based, and internally consistent
- Critical feedback as a structured list citing which quality standard is violated
- No rewriting — critique only, the PM does the revisions

---

## Files Summary

| Action | File |
|--------|------|
| MODIFY | `src/schema.py` — add `knowledge_sources` to JSON_SCHEMA, STEP_TYPES unchanged, add validation |
| MODIFY | `src/render.py` — add `_knowledge_sources_table()` and KB protocol rendering |
| MODIFY | `workflow/orchestrator-debate.yaml` — add `knowledge_sources` section |
| NEW | `workflow/product-squad.yaml` — full product squad workflow |
| NEW | `agents/product/product-lead.md` — squad leader agent definition |
| NEW | `agents/product/product-manager.md` — PRD writer agent definition |
| NEW | `agents/product/product-critic.md` — adversarial reviewer agent definition |
| GENERATED | `workflow/product-squad.md` — rendered via `make apply` |
| REGENERATED | `workflow/orchestrator-debate.md` — re-rendered via `make apply` |

## Verification Plan

1. Run `python -m src.cli validate workflow/product-squad.yaml` — must pass
2. Run `python -m src.cli validate workflow/orchestrator-debate.yaml` — must pass (with new `knowledge_sources`)
3. Run `python -m src.cli apply workflow/product-squad.yaml` — generates `product-squad.md` with Knowledge Sources table and KB Protocol section
4. Run `python -m src.cli apply workflow/orchestrator-debate.yaml` — re-generates `orchestrator-debate.md` with Knowledge Sources table
5. Visually verify the Mermaid diagram renders correctly for the product squad workflow
6. Verify the KB Protocol section lists correct sources for read vs write access

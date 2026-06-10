# Three-Agent Coding Pipeline Design

**Date:** 2026-06-10  
**Status:** Approved for Implementation  
**Related Workflow:** `workflow/development.yaml`

---

## Problem Statement

The current `coder-agent` combines exploration, planning, and implementation in a single agent using an expensive model for all phases. This is suboptimal for cost and separation of concerns.

**Goals:**
1. Cost optimization: Use expensive model only for planning/review
2. Better separation of concerns: Each agent has single responsibility
3. Explicit plan-compliance verification: Planner reviews implementation matches plan

---

## Agent Definitions

### 1. Code-Explorer Agent (`agents/coding/code-explorer-agent.md`)

| Property | Value |
|----------|-------|
| **Model** | Cheap (e.g., GPT-4o-mini, Claude Haiku) |
| **Role** | Codebase exploration & context gathering |
| **Access** | Read-only repository access |
| **Input** | Task description |
| **Output** | Structured context package (JSON):<br/>- `architecture_summary`: 3-5 sentences<br/>- `relevant_files`: `[{path, purpose, key_snippets}]`<br/>- `patterns`: coding conventions, idioms<br/>- `dependencies`: internal/external<br/>- `risks`: potential issues |

**Responsibilities:**
- Explore repository structure
- Identify files relevant to the task
- Extract key interfaces, patterns, conventions
- Produce concise context package for Planner

**Non-Responsibilities:**
- No planning
- No code writing
- No architectural decisions

---

### 2. Code-Planner Agent (`agents/coding/code-planner-agent.md`)

| Property | Value |
|----------|-------|
| **Model** | Expensive (best reasoning: GPT-4o, Claude Opus) |
| **Role** | Detailed implementation planning + plan-compliance review |
| **Access** | None (relies entirely on Explorer output) |
| **Input (Planning)** | Task + Explorer context package |
| **Output (Planning)** | Implementation Plan (JSON):<br/>- `architecture_decisions`: key choices with rationale<br/>- `file_changes`: `[{path, action: create|modify|delete, description}]`<br/>- `tdd_plan`: `[{test_file, test_cases, mocking_strategy}]`<br/>- `implementation_order`: ordered file list<br/>- `risks`: mitigation strategies |
| **Input (Review)** | Approved Implementation Plan + Execution Results (diff, test output) |
| **Output (Review)** | Compliance Report (JSON):<br/>- `plan_matched`: boolean<br/>- `deviations`: list of differences with severity<br/>- `missing_tests`: planned tests not implemented<br/>- `architectural_compliance`: boolean<br/>- `recommendations`: fixes if needed |

**Responsibilities (Planning Phase):**
- Analyze task + context
- Produce detailed, actionable implementation plan
- Debate plan with Code-Critic (multi-turn)
- Incorporate critic feedback

**Responsibilities (Review Phase):**
- Verify implementation matches approved plan
- Check all planned files were changed
- Verify TDD tests match plan
- Validate architectural decisions followed
- Produce compliance report for HITL

**Non-Responsibilities:**
- No code execution
- No direct codebase access
- No test running

---

### 3. Code-Implementer Agent (`agents/coding/code-implementer-agent.md`)

| Property | Value |
|----------|-------|
| **Model** | Cheap (same tier as Explorer) |
| **Role** | TDD implementation execution |
| **Access** | Full repository access (read/write/search) |
| **Input** | Approved Implementation Plan |
| **Output** | Execution Results:<br/>- Failing tests created (Red phase)<br/>- Implementation making tests pass (Green phase)<br/>- Lint/typecheck passing<br/>- Runbook (5 sections: Symptoms, Diagnosis, Remediation, Verification, Escalation)<br/>- Conventional commit message |

**Responsibilities:**
- Write tests first per TDD plan
- Implement code to pass tests
- Run lint/typecheck
- Create runbook
- Follow plan strictly; deviations require explicit justification in output

**Non-Responsibilities:**
- No planning
- No architectural decisions
- No plan compliance review (done by Planner)

---

## Workflow Integration

### Modified `development.yaml` Steps

```yaml
# Existing: PM breaks down tasks
- id: implementation-planning
  type: delegate
  actor: pm-agent
  input: srs
  output: task-breakdown

# NEW: Explorer + Planner in parallel
- id: worker-plans
  type: fanout
  input: task-breakdown
  workers:
    - id: explore-context
      actor: code-explorer-agent
      output: codebase-context
    - id: plan-implementation
      actor: code-planner-agent
      input: codebase-context
      output: draft-implementation-plan

# NEW: Planner debates plan with Code-Critic
- id: planner-debate
  type: debate
  actor: code-planner-agent
  critic: code-critic-agent
  artifact: draft-implementation-plan
  max_turn: 3
  on_approved: implementation-execution
  on_max_turn_reached: hitl

# REPLACES: Old execution step (coder-agent + qa-agent)
- id: implementation-execution
  type: delegate
  actor: code-implementer-agent
  input: approved-implementation-plan
  output: execution-results
  max_turn: 3

# NEW: Planner reviews implementation compliance
- id: plan-compliance-review
  type: delegate
  actor: code-planner-agent
  input:
    - approved-implementation-plan
    - execution-results
  output: compliance-report

# Existing: DevOps CI/CD
- id: cicd-setup
  type: delegate
  actor: devops-agent
  input: test-suites
  output: cicd-pipeline

# Existing: Human review (now includes compliance-report)
- id: hitl-execution
  type: hitl
  artifact: execution-results + compliance-report
  on_approved: completion
  on_rejected: implementation-execution
```

### Removed Steps
- `worker-plans` old `coder-plan` worker (replaced by explore-context + plan-implementation)
- `implementation-debate` (coder-agent vs code-critic-agent on plan) — replaced by `planner-debate`

---

## Data Contracts

### Explorer → Planner: `codebase-context`
```json
{
  "architecture_summary": "string",
  "relevant_files": [
    {"path": "string", "purpose": "string", "key_snippets": ["string"]}
  ],
  "patterns": ["string"],
  "dependencies": ["string"],
  "risks": ["string"]
}
```

### Planner → Critic/Implementer: `implementation-plan`
```json
{
  "architecture_decisions": [
    {"decision": "string", "rationale": "string", "alternatives_considered": ["string"]}
  ],
  "file_changes": [
    {"path": "string", "action": "create|modify|delete", "description": "string"}
  ],
  "tdd_plan": [
    {"test_file": "string", "test_cases": ["string"], "mocking_strategy": "string"}
  ],
  "implementation_order": ["string"],
  "risks": [{"risk": "string", "mitigation": "string"}]
}
```

### Implementer → Planner (Review): `execution-results`
```json
{
  "diff": "string",
  "test_results": "object",
  "lint_results": "object",
  "runbook": "string",
  "commit_message": "string"
}
```

### Planner → HITL: `compliance-report`
```json
{
  "plan_matched": true,
  "deviations": [
    {"file": "string", "expected": "string", "actual": "string", "severity": "major|minor"}
  ],
  "missing_tests": ["string"],
  "architectural_compliance": true,
  "recommendations": ["string"]
}
```

---

## Cost Model

| Agent | Model Tier | Relative Cost |
|-------|-----------|---------------|
| Code-Explorer | Cheap | 0.1x |
| Code-Planner | Expensive | 1.0x (runs twice: plan + review) |
| Code-Implementer | Cheap | 0.1x |
| **Total** | | **~1.2x expensive-model-equivalent** |

**Comparison:** Old coder-agent used expensive model for explore + plan + implement + debate (~3-4x expensive-model-equivalent).  
**Savings:** ~60-70% reduction in expensive model usage.

---

## Migration Path

1. Create three new agent markdown files
2. Update `development.yaml` with new steps
3. Test with a small task
4. Deprecate `coder-agent.md` and `code-critic-agent.md` (critic still used for planner-debate)
5. Update any references in documentation

---

## Open Questions (Resolved)

1. **Planner codebase access?** → No, relies on Explorer output only
2. **Implementer codebase access?** → Full read/write/search, guided by plan
3. **Post-implementation review?** → Planner does plan-compliance review
4. **Critic involvement?** → Code-Critic debates Planner's plan (multi-turn)
5. **Handoff pattern?** → Sequential pipeline: Explorer → Planner → Implementer → Planner(review)

---

## Approval

- [x] Design reviewed and approved
- [ ] Implementation plan created (next step: invoke `writing-plans` skill)
- [ ] Agents created
- [ ] Workflow updated
- [ ] Tests pass
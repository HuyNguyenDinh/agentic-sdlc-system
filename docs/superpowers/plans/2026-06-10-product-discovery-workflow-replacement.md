# Product Discovery Workflow Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the simple product squad workflow with a hybrid product discovery workflow that performs parallel research and business analysis, persists artifacts and human decisions, and hands a development-ready package to the development squad.

**Architecture:** Keep the existing workflow schema and engine concepts: `delegate`, `fanout`, `debate`, and `hitl`. Add two product specialist agent files, update existing product agents, replace `workflow/product.yaml`, render `workflow/product.md`, and adjust the Mermaid renderer so fanout worker labels describe their actual outputs instead of always saying `plans`.

**Tech Stack:** Python standard library `unittest`, PyYAML, existing CLI module `src.cli`, existing workflow validator `src.core.services.workflow_service`, existing Markdown renderer `src.adapters.markdown_renderer`.

---

## File Structure

- Create `tests/test_markdown_renderer.py`: focused renderer regression tests for fanout worker labels.
- Modify `src/adapters/markdown_renderer.py`: replace hardcoded fanout worker label `plans` with the worker `output` value.
- Create `tests/test_product_workflow_replacement.py`: product workflow contract tests that validate agents, steps, knowledge sources, artifacts, persistence language, and rendered markdown.
- Modify `agents/product/product-lead-agent.md`: make the lead responsible for intake normalization, orchestration, artifact persistence, HITL decision capture, and handoff.
- Modify `agents/product/product-manager-agent.md`: make the PM responsible for PRD and development-ready package synthesis from discovery artifacts.
- Create `agents/product/product-research-agent.md`: customer, partner, support, feedback, and analytics research specialist.
- Create `agents/product/business-strategy-agent.md`: business strategy, roadmap, priority, and partner impact specialist.
- Modify `agents/product/product-critic-agent.md`: review PRD and development-ready package quality, evidence strength, business alignment, and handoff clarity.
- Replace `workflow/product.yaml`: new canonical product workflow.
- Regenerate `workflow/product.md`: generated Markdown from `workflow/product.yaml`.

---

### Task 1: Add Renderer Fanout Regression Test

**Files:**
- Create: `tests/test_markdown_renderer.py`
- Test: `tests/test_markdown_renderer.py`

- [ ] **Step 1: Write the failing renderer test**

Create `tests/test_markdown_renderer.py` with this content:

```python
import unittest

from src.adapters.markdown_renderer import render_mermaid


class TestMarkdownRenderer(unittest.TestCase):
    def test_fanout_worker_labels_use_worker_outputs(self):
        data = {
            "workflow": {
                "name": "product-squad",
                "squad_leader": "product-lead-agent",
                "max_turn": 3,
            },
            "agents": [
                {
                    "id": "product-lead-agent",
                    "role": "Product Lead",
                    "path": "agents/product/product-lead-agent.md",
                },
                {
                    "id": "product-research-agent",
                    "role": "Research Analyst",
                    "path": "agents/product/product-research-agent.md",
                },
                {
                    "id": "business-strategy-agent",
                    "role": "Business Strategy Analyst",
                    "path": "agents/product/business-strategy-agent.md",
                },
            ],
            "steps": [
                {
                    "id": "intake-normalization",
                    "type": "delegate",
                    "description": "Normalize product input",
                    "actor": "product-lead-agent",
                    "output": "intake-brief",
                },
                {
                    "id": "discovery-fanout",
                    "type": "fanout",
                    "description": "Research and strategy specialists work in parallel",
                    "input": "intake-brief",
                    "workers": [
                        {
                            "id": "research",
                            "actor": "product-research-agent",
                            "output": "evidence-summary",
                        },
                        {
                            "id": "strategy",
                            "actor": "business-strategy-agent",
                            "output": "business-alignment-brief",
                        },
                    ],
                },
            ],
        }

        mermaid = render_mermaid(data)

        self.assertIn('discovery-fanout_research["Research Analyst<br/>evidence summary"]', mermaid)
        self.assertIn('discovery-fanout_strategy["Business Strategy Analyst<br/>business alignment brief"]', mermaid)
        self.assertIn('discovery-fanout_merge[("Fanout Outputs<br/>Ready")]', mermaid)
        self.assertNotIn("<br/>plans", mermaid)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_markdown_renderer -v
```

Expected: FAIL because `render_mermaid()` currently renders fanout worker nodes with `<br/>plans` and merge node text `Plans<br/>Ready`.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_markdown_renderer.py
git commit -m "test: cover fanout worker output labels"
```

---

### Task 2: Render Fanout Outputs Accurately

**Files:**
- Modify: `src/adapters/markdown_renderer.py`
- Test: `tests/test_markdown_renderer.py`

- [ ] **Step 1: Implement fanout output labels**

In `src/adapters/markdown_renderer.py`, replace the `elif stype == "fanout":` block with this implementation:

```python
        elif stype == "fanout":
            node = f"step_{sid}"
            label = f"{step_num}. {desc}"
            lines.append(f"    {node}[\"{label}\"]")
            lines.append(f"    {prev_node} --> {node}")

            worker_nodes = []
            for w in step.get("workers", []):
                wid = f"{sid}_{w['id']}"
                worker_label = _agent_display(w["actor"], agents)
                output_label = _label(w.get("output", "work").replace("-", " "), width=24)
                lines.append(f"    {wid}[\"{worker_label}<br/>{output_label}\"]")
                lines.append(f"    {node} --> {wid}")
                worker_nodes.append(wid)

            merge_node = f"{sid}_merge"
            lines.append(f"    {merge_node}[(\"Fanout Outputs<br/>Ready\")]")
            for wn in worker_nodes:
                lines.append(f"    {wn} --> {merge_node}")

            nodes.append(node)
            prev_node = merge_node
```

- [ ] **Step 2: Run the renderer test**

Run:

```bash
python -m unittest tests.test_markdown_renderer -v
```

Expected: PASS.

- [ ] **Step 3: Run existing unit tests**

Run:

```bash
python -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 4: Commit renderer change**

```bash
git add src/adapters/markdown_renderer.py
git commit -m "fix: render fanout worker outputs"
```

---

### Task 3: Add Product Workflow Contract Tests

**Files:**
- Create: `tests/test_product_workflow_replacement.py`
- Test: `tests/test_product_workflow_replacement.py`

- [ ] **Step 1: Write failing product workflow tests**

Create `tests/test_product_workflow_replacement.py` with this content:

```python
import unittest
from pathlib import Path

import yaml

from src.adapters.markdown_renderer import render_markdown
from src.core.services.workflow_service import validate


PRODUCT_YAML = Path("workflow/product.yaml")


class TestProductWorkflowReplacement(unittest.TestCase):
    def setUp(self):
        self.data = yaml.safe_load(PRODUCT_YAML.read_text())

    def test_product_workflow_validates(self):
        self.assertEqual(validate(self.data), [])

    def test_hybrid_product_agents_are_declared(self):
        agent_ids = {agent["id"] for agent in self.data["agents"]}

        self.assertEqual(self.data["workflow"]["squad_leader"], "product-lead-agent")
        self.assertTrue(
            {
                "product-lead-agent",
                "product-manager-agent",
                "product-research-agent",
                "business-strategy-agent",
                "product-critic-agent",
            }.issubset(agent_ids)
        )

    def test_workflow_steps_match_approved_design(self):
        steps = self.data["steps"]
        self.assertEqual(
            [step["id"] for step in steps],
            [
                "intake-normalization",
                "discovery-fanout",
                "artifact-persistence-discovery",
                "prd-synthesis",
                "prd-package-debate",
                "artifact-persistence-prd",
                "final-prd-review",
                "decision-persistence",
                "development-handoff",
            ],
        )

        by_id = {step["id"]: step for step in steps}
        self.assertEqual(by_id["discovery-fanout"]["type"], "fanout")
        self.assertEqual(
            [worker["actor"] for worker in by_id["discovery-fanout"]["workers"]],
            ["product-research-agent", "business-strategy-agent"],
        )
        self.assertEqual(
            [worker["output"] for worker in by_id["discovery-fanout"]["workers"]],
            ["evidence-summary", "business-alignment-brief"],
        )
        self.assertEqual(by_id["prd-package-debate"]["type"], "debate")
        self.assertEqual(by_id["final-prd-review"]["type"], "hitl")
        self.assertEqual(by_id["final-prd-review"]["on_approved"], "decision-persistence")
        self.assertEqual(by_id["final-prd-review"]["on_rejected"], "prd-synthesis")

    def test_knowledge_sources_cover_research_strategy_and_persistence(self):
        sources = {source["id"]: source for source in self.data["knowledge_sources"]}

        self.assertEqual(sources["llm-wiki"]["access"], ["read", "write"])
        self.assertEqual(sources["customer-feedback"]["access"], ["read"])
        self.assertEqual(sources["partner-input"]["access"], ["read"])
        self.assertEqual(sources["business-strategy"]["access"], ["read"])

    def test_rendered_markdown_mentions_artifacts_persistence_and_handoff(self):
        markdown = render_markdown(self.data, yaml_rel="product.yaml")

        expected_phrases = [
            "Product Research Analyst",
            "Business Strategy Analyst",
            "intake brief, evidence summary, and business alignment brief",
            "stores draft PRD/package versions, critique outcomes, and unresolved findings",
            "stores the human decision, rationale, reviewer identity",
            "hands it to the development squad",
            "development-ready package",
            "partner-input",
            "business-strategy",
        ]
        for phrase in expected_phrases:
            self.assertIn(phrase, markdown)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_product_workflow_replacement -v
```

Expected: FAIL because the current product workflow does not declare the two new specialist agents, does not use the new step sequence, and does not render the approved persistence language.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_product_workflow_replacement.py
git commit -m "test: cover product discovery workflow replacement"
```

---

### Task 4: Update Product Agent Definitions

**Files:**
- Modify: `agents/product/product-lead-agent.md`
- Modify: `agents/product/product-manager-agent.md`
- Create: `agents/product/product-research-agent.md`
- Create: `agents/product/business-strategy-agent.md`
- Modify: `agents/product/product-critic-agent.md`
- Test: `tests/test_product_workflow_replacement.py`

- [ ] **Step 1: Replace Product Lead definition**

Replace `agents/product/product-lead-agent.md` with:

```markdown
# Product Lead Agent

**Role:** Squad Leader & Orchestrator for the Product Discovery Squad.

## Responsibilities
- Accept raw human requests or structured intake packets.
- Normalize inputs into an `intake-brief` with problem, requester, stakeholders, assumptions, constraints, missing information, and initial scope boundary.
- Route discovery work to Research and Business Strategy specialists in parallel.
- Enforce workflow phase boundaries and `{MAX_TURN}` debate limits.
- Trigger the final HITL review for the PRD and development-ready package.
- Persist every meaningful artifact to writable knowledge sources.
- Persist human approvals, rejections, clarifications, and rationale to writable knowledge sources.
- Package and hand off approved product work to the development squad.

## Knowledge Base Interaction
- Before orchestration: query LLM-WIKI for prior decisions, related PRDs, known stakeholder constraints, and relevant strategy context.
- During orchestration: ensure `intake-brief`, `evidence-summary`, `business-alignment-brief`, PRD drafts, critique outcomes, final PRD, decision records, and handoff package are stored in writable knowledge sources.
- Mark draft artifacts as draft or superseded when later versions replace them.
- Maintain cross-references between human decisions, source evidence, PRD sections, and development handoff artifacts.

## Constraints
- Centralized communication: all inter-agent workflow routing flows through this agent.
- Does not write the PRD directly.
- Does not hide unresolved critic findings from human review.
- Does not treat missing evidence as proof. Missing sources must be recorded as gaps.
```

- [ ] **Step 2: Replace Product Manager definition**

Replace `agents/product/product-manager-agent.md` with:

```markdown
# Product Manager Agent

**Role:** Product Owner / Product Manager and PRD Package Writer.

## Responsibilities
- Synthesize the `intake-brief`, `evidence-summary`, and `business-alignment-brief` into a clear PRD.
- Produce a development-ready package that includes approved PRD content, epics, user stories, acceptance criteria, non-goals, risks, open questions, evidence links, decision log references, and suggested parallel implementation workstreams.
- Respond to Product Critic feedback with evidence-based revisions or explicit tradeoff notes.
- Preserve conflicting evidence and unresolved questions in the package instead of removing them.

## Knowledge Base Interaction
- Before synthesis: query LLM-WIKI for prior PRDs, decisions, glossary terms, patterns, and related delivery outcomes.
- During synthesis: cite customer, partner, feedback, analytics, and business strategy evidence used in the PRD.
- After synthesis: provide the Product Lead with artifact content suitable for persistence.

## Quality Standards
- Requirements must be concrete, measurable, and testable.
- User stories must use `As a [user], I want to [action] so that [benefit]`.
- Acceptance criteria must define observable done conditions.
- Non-goals must protect scope and identify excluded behavior.
- Suggested implementation workstreams must be independent enough for parallel development planning.
```

- [ ] **Step 3: Create Product Research definition**

Create `agents/product/product-research-agent.md` with:

```markdown
# Product Research Agent

**Role:** Product Research Analyst for customer, partner, feedback, support, and usage evidence.

## Responsibilities
- Analyze the `intake-brief` for research questions, evidence needs, missing customer context, and partner dependencies.
- Query customer feedback, support tickets, partner inputs, usage analytics, and LLM-WIKI where available.
- Produce an `evidence-summary` with source citations, confidence level, evidence gaps, and conflicting signals.
- Separate observed evidence from inference.
- Avoid writing PRD requirements directly.

## Knowledge Base Interaction
- Before research: query readable knowledge sources for related feedback, user pain, partner commitments, known incidents, and prior discovery notes.
- After research: provide the Product Lead with an `evidence-summary` suitable for persistence to writable knowledge sources.

## Output Standards
- Include evidence grouped by customer, partner, support, usage, and prior knowledge when sources are available.
- Mark unavailable sources explicitly.
- Mark confidence as high, medium, or low with a short reason.
- Preserve contradictions and weak signals.
```

- [ ] **Step 4: Create Business Strategy definition**

Create `agents/product/business-strategy-agent.md` with:

```markdown
# Business Strategy Agent

**Role:** Business Strategy Analyst for roadmap, priority, constraints, partner impact, and expected outcomes.

## Responsibilities
- Analyze the `intake-brief` against business goals, roadmap context, strategy constraints, partner impact, and expected outcomes.
- Produce a `business-alignment-brief` with strategic fit, priority rationale, constraints, risks, and success metrics.
- Identify business assumptions that need human confirmation.
- Avoid writing PRD requirements directly.

## Knowledge Base Interaction
- Before analysis: query LLM-WIKI and business strategy sources for roadmap priorities, strategic decisions, partner commitments, and constraints.
- After analysis: provide the Product Lead with a `business-alignment-brief` suitable for persistence to writable knowledge sources.

## Output Standards
- State whether the request aligns with current business priorities.
- Include expected business outcome and measurable success signals.
- Identify risks, tradeoffs, and partner impact.
- Mark unavailable strategy sources explicitly.
```

- [ ] **Step 5: Replace Product Critic definition**

Replace `agents/product/product-critic-agent.md` with:

```markdown
# Product Critic Agent

**Role:** Adversarial Reviewer for PRDs and development-ready product packages.

## Responsibilities
- Review PRDs and development-ready packages for weak evidence, vague requirements, missing edge cases, scope creep, feasibility risk, business misalignment, and unclear handoff.
- Validate claims against available knowledge sources and supplied discovery artifacts.
- Challenge unsupported assumptions without rewriting the PRD.
- Approve only when the package is evidence-based, internally consistent, testable, and ready for development squad handoff.

## Knowledge Base Interaction
- Before reviewing: query LLM-WIKI for related decisions, prior failures, existing PRDs, and delivery lessons.
- During review: compare PRD claims with the `evidence-summary` and `business-alignment-brief`.
- After review: provide critique outcomes to the Product Lead for persistence.

## Review Lenses
1. Evidence Quality: requirements trace to customer, partner, usage, support, or business evidence.
2. Requirement Testability: acceptance criteria are observable and measurable.
3. Stakeholder Ambiguity: unclear decisions or missing approvers are flagged.
4. Scope Discipline: non-goals and exclusions are explicit.
5. Business Alignment: strategic fit, partner impact, and success metrics are coherent.
6. Handoff Clarity: epics, stories, risks, open questions, and suggested workstreams are ready for development planning.

## Output Constraints
- Return `SUCCESS` only when the PRD package satisfies the review lenses.
- Return structured findings grouped by review lens when rejecting.
- Attach unresolved findings when `{MAX_TURN}` is reached.
- Do not rewrite the PRD; the Product Manager owns revisions.
```

- [ ] **Step 6: Run product workflow tests to keep expected failure localized**

Run:

```bash
python -m unittest tests.test_product_workflow_replacement -v
```

Expected: FAIL remains until `workflow/product.yaml` is replaced, but failures about missing agent files should be gone if the test runner or future tests inspect paths.

- [ ] **Step 7: Commit product agent updates**

```bash
git add agents/product/product-lead-agent.md agents/product/product-manager-agent.md agents/product/product-research-agent.md agents/product/business-strategy-agent.md agents/product/product-critic-agent.md
git commit -m "feat: define hybrid product discovery agents"
```

---

### Task 5: Replace Product Workflow YAML

**Files:**
- Modify: `workflow/product.yaml`
- Test: `tests/test_product_workflow_replacement.py`

- [ ] **Step 1: Replace `workflow/product.yaml`**

Replace `workflow/product.yaml` with:

```yaml
workflow:
  name: product-squad
  description: >
    Product Lead-orchestrated discovery workflow that normalizes human input,
    runs research and business strategy analysis in parallel, synthesizes a PRD
    plus development-ready package, captures final human approval, persists
    artifacts and decisions, and hands approved work to the development squad.

  max_turn: 3
  squad_leader: product-lead-agent

agents:
  - id: product-lead-agent
    role: Product Lead & Orchestrator
    path: agents/product/product-lead-agent.md

  - id: product-manager-agent
    role: Product Owner / Product Manager
    path: agents/product/product-manager-agent.md

  - id: product-research-agent
    role: Product Research Analyst
    path: agents/product/product-research-agent.md

  - id: business-strategy-agent
    role: Business Strategy Analyst
    path: agents/product/business-strategy-agent.md

  - id: product-critic-agent
    role: Product Critic & Reviewer
    path: agents/product/product-critic-agent.md

knowledge_sources:
  - id: llm-wiki
    type: wiki
    description: Obsidian-based organizational knowledge base for prior decisions, product artifacts, decision logs, and reusable product knowledge
    access: [read, write]

  - id: customer-feedback
    type: external
    description: Customer feedback, support tickets, and usage analytics
    access: [read]

  - id: partner-input
    type: external
    description: Partner documents, partner constraints, commitments, and collaboration context
    access: [read]

  - id: business-strategy
    type: external
    description: Business goals, roadmap context, priorities, strategic constraints, and expected outcomes
    access: [read]

steps:
  - id: intake-normalization
    type: delegate
    description: Product Lead normalizes raw human request or structured packet into an intake brief
    actor: product-lead-agent
    output: intake-brief

  - id: discovery-fanout
    type: fanout
    description: Research and strategy specialists work in parallel from the same intake brief
    input: intake-brief
    workers:
      - id: research
        actor: product-research-agent
        output: evidence-summary

      - id: strategy
        actor: business-strategy-agent
        output: business-alignment-brief

  - id: artifact-persistence-discovery
    type: delegate
    description: Product Lead stores the intake brief, evidence summary, and business alignment brief in writable knowledge sources
    actor: product-lead-agent
    input: discovery-artifacts
    output: persisted-discovery-artifacts

  - id: prd-synthesis
    type: delegate
    description: Product Manager creates PRD plus development-ready package from intake, evidence, and business alignment
    actor: product-manager-agent
    input: persisted-discovery-artifacts
    output: draft-development-ready-package

  - id: prd-package-debate
    type: debate
    description: Product Manager and Critic debate PRD package quality, evidence, business alignment, and handoff clarity
    actor: product-manager-agent
    critic: product-critic-agent
    input: draft-development-ready-package
    artifact: reviewed-development-ready-package
    max_turn: 3
    on_approved: artifact-persistence-prd
    on_max_turn_reached: artifact-persistence-prd

  - id: artifact-persistence-prd
    type: delegate
    description: Product Lead stores draft PRD/package versions, critique outcomes, and unresolved findings
    actor: product-lead-agent
    input: reviewed-development-ready-package
    output: persisted-prd-package

  - id: final-prd-review
    type: hitl
    description: Human reviews final candidate PRD and development-ready package
    artifact: persisted-prd-package
    on_approved: decision-persistence
    on_rejected: prd-synthesis

  - id: decision-persistence
    type: delegate
    description: Product Lead stores the human decision, rationale, reviewer identity if available, timestamp, and approved or rejected artifact references
    actor: product-lead-agent
    input: human-decision
    output: persisted-human-decision

  - id: development-handoff
    type: delegate
    description: Product Lead stores the final approved development-ready package and hands it to the development squad
    actor: product-lead-agent
    input: approved-development-ready-package
    output: product-handoff-package
```

- [ ] **Step 2: Validate product workflow**

Run:

```bash
python -m src.cli validate workflow/product.yaml
```

Expected output includes:

```text
✓ workflow/product.yaml is valid
```

- [ ] **Step 3: Run product workflow tests**

Run:

```bash
python -m unittest tests.test_product_workflow_replacement -v
```

Expected: PASS.

- [ ] **Step 4: Commit product workflow YAML**

```bash
git add workflow/product.yaml
git commit -m "feat: replace product workflow with discovery squad"
```

---

### Task 6: Regenerate Product Workflow Markdown

**Files:**
- Modify: `workflow/product.md`
- Test: `workflow/product.md`

- [ ] **Step 1: Render markdown from YAML**

Run:

```bash
python -m src.cli apply workflow/product.yaml
```

Expected output includes:

```text
Applied: workflow/product.yaml
```

- [ ] **Step 2: Verify rendered markdown contains required content**

Run:

```bash
rg -n "Product Research Analyst|Business Strategy Analyst|artifact-persistence-discovery|decision-persistence|development-ready package|partner-input|business-strategy" workflow/product.md
```

Expected: matches for each searched concept in `workflow/product.md`.

- [ ] **Step 3: Run product workflow tests after rendering**

Run:

```bash
python -m unittest tests.test_product_workflow_replacement -v
```

Expected: PASS.

- [ ] **Step 4: Commit generated markdown**

```bash
git add workflow/product.md
git commit -m "docs: render product discovery workflow"
```

---

### Task 7: Final Verification

**Files:**
- Verify: `src/adapters/markdown_renderer.py`
- Verify: `workflow/product.yaml`
- Verify: `workflow/product.md`
- Verify: `agents/product/*.md`
- Verify: `tests/test_markdown_renderer.py`
- Verify: `tests/test_product_workflow_replacement.py`

- [ ] **Step 1: Run full unit test suite**

Run:

```bash
python -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 2: Run legacy schema test module**

Run:

```bash
python src/test_schema.py
```

Expected output includes:

```text
✓ All validation tests pass successfully!
```

- [ ] **Step 3: Validate product and development workflows**

Run:

```bash
python -m src.cli validate workflow/product.yaml
python -m src.cli validate workflow/development.yaml
```

Expected output includes:

```text
✓ workflow/product.yaml is valid
✓ workflow/development.yaml is valid
```

- [ ] **Step 4: Check git status**

Run:

```bash
git status --short
```

Expected: no output.

- [ ] **Step 5: Report final commit list**

Run:

```bash
git log --oneline -6
```

Expected: output includes these implementation commits:

```text
docs: render product discovery workflow
feat: replace product workflow with discovery squad
feat: define hybrid product discovery agents
test: cover product discovery workflow replacement
fix: render fanout worker outputs
test: cover fanout worker output labels
```

---

## Self-Review

Spec coverage:
- Workflow replacement: Task 5 replaces `workflow/product.yaml`; Task 6 regenerates `workflow/product.md`.
- Hybrid agent roster: Task 4 creates or updates all five agents; Task 3 tests their declaration.
- Parallel research and strategy workstreams: Task 5 uses `fanout`; Task 1 and Task 2 ensure fanout output labels are accurate.
- Artifact persistence: Task 5 adds `artifact-persistence-discovery` and `artifact-persistence-prd`; Task 3 asserts persistence language is rendered.
- Human decision persistence: Task 5 adds `decision-persistence`; Task 3 asserts decision persistence language is rendered.
- Final HITL only: Task 5 includes one `hitl` step, `final-prd-review`.
- Development-ready package handoff: Task 5 adds `development-handoff`; Task 3 asserts handoff language is rendered.
- No schema change: all tasks use existing step types and validation commands.

Placeholder scan:
- The plan contains no unresolved markers, no incomplete file list, and no missing command outputs.

Type consistency:
- Step IDs in tests match the YAML in Task 5.
- Agent IDs in tests, YAML, and agent file paths match.
- Worker outputs in tests match YAML outputs.
- Renderer test expectations match the exact output labels produced by the Task 2 renderer change.

# Three-Tier QA Agent Cost Optimization Design

**Date:** 2026-06-14
**Status:** Approved for Implementation
**Source:** Based on [petrkindlmann/qa-skills](https://github.com/petrkindlmann/qa-skills) v3.0.0 (50 skills)

---

## Problem Statement

The current `qa-agent` does everything in 2 broad phases (Planning + Execution), using a single expensive model for all work. The `qa-critic-agent` then debates the plan. This is wasteful:

1. **Cost:** Context gathering and test generation don't need an expensive reasoning model
2. **Quality:** No risk-based prioritization, no coverage matrix, no test review pass
3. **Scope:** No structured test artifacts (strategy, plan, coverage matrix, review report), so HITL has no evidence to evaluate
4. **Ambiguity:** The old "Execution" phase conflated code generation with execution, but QA never executes tests -- DevOps owns CI/CD execution

**Goal:** Split QA into three cost-tier agents that map to the qa-skills pipeline, keep `qa-critic` for debate quality, and route DevOps-owned CI/CD metrics back to HITL.

---

## Scope

- Backend/API-focused QA phases only (no UI/E2E/visual/performance yet)
- Extensible hooks for future full-stack QA roles (see Extension Hooks)
- `qa-critic-agent` retained for adversarial debate on plans
- `devops-agent` owns pipeline plumbing; QA defines all metrics, artifacts, and execution commands
- HITL receives structured reports from QA and DevOps for release gate decisions

---

## Responsibility Split

| Concern | QA Owns | DevOps Owns |
|---------|---------|-------------|
| Test structure, naming, tags | QA -- defines the test suite layout | Wires the glob patterns into pipeline jobs |
| Coverage thresholds | QA -- sets the % (e.g. 80% lines, 70% branches) | Configures `coverageThreshold` in CI config, gates PRs |
| Flakiness definition | QA -- defines `@flaky` tag convention, quarantine criteria | Creates quarantine job (`--grep @flaky`), runs nightly |
| Artifact format | QA -- specifies JUnit XML, HTML report, trace format | Uploads artifacts (`upload-artifact@v7`), sets retention |
| Execution commands | QA -- writes the exact `npx playwright test --shard` command per test type | Pastes it into the workflow YAML, adds matrix sharding |
| Metrics/KPIs | QA -- defines formulas (defect escape rate, flakiness %, coverage trend) and output format | Collects raw data from pipeline, exports as structured artifact |
| Report schema | QA -- defines the `qa-review-report.json` schema, `test-execution-evidence.json` schema | Merges sharded reports, publishes to PR/HITL |
| Environment requirements | QA -- specifies DB version, mock services, seed data shape | Creates docker-compose, provisions env |
| Security scan config | QA -- writes the OWASP ZAP YAML rules, sets severity thresholds | Runs ZAP in CI scheduled job, fails on threshold |

---

## Agent Definitions

### 1. QA-Context+Risk Agent (`agents/qa/qa-context-risk-agent.md`)

| Property | Value |
|----------|-------|
| **Model** | Cheap (Haiku 4.5 / GPT-4o-mini) |
| **Role** | Project context extraction + risk assessment |
| **Access** | Read repository, read SRS/PRD |
| **Input** | Task breakdown, codebase context, SRS, development.yaml |
| **Output** | `qa-project-context.md` + `risk-matrix` |

**Responsibilities (mapped from qa-skills):**
- `qa-project-context` -- capture tech stack, test frameworks, CI/CD, environments, quality goals, team maturity
- Risk identification -- enumerate what could go wrong: stakeholder interviews, incident history, dependency mapping, change analysis
- Risk classification -- score impact (1-5) x probability (1-5), produce composite score per feature area
- Failure mode analysis -- for every item scoring >= 10: trigger, blast radius, detection method, current mitigation, gap
- Output a scored risk heatmap (CRITICAL/HIGH/MEDIUM/LOW per feature) and the qa-project-context file

**Model routing rationale:** These are mechanical extraction/classification tasks. A cheap model is sufficient.

---

### 2. QA-Planner Agent (`agents/qa/qa-planner-agent.md`)

| Property | Value |
|----------|-------|
| **Model** | Expensive (Opus 4.8 / GPT-4o) |
| **Role** | Test strategy + sprint/release test planning |
| **Access** | Read qa-project-context.md + risk-matrix (no direct repo access) |
| **Input** | qa-project-context + risk-matrix + task-breakdown + implementation-plan |
| **Output** | `test-strategy` + `test-plan` + `coverage-matrix` |

**Responsibilities (mapped from qa-skills):**
- `test-strategy` -- multi-quarter direction: scope, test levels, pyramid analysis, entry/exit criteria, quality KPIs, tool selection rationale, timeline/milestones
- `test-planning` -- sprint/release plan: feature decomposition into testable scenarios, requirements-to-test mapping, effort estimation, risk x effort prioritization, resource allocation, buffer scheduling
- `coverage matrix` -- map every requirement to at least one scenario; mark gaps; assign priority (P0-P3)
- Output a consolidated test plan with BDD Gherkin scenarios (Given-When-Then), specified tools (Karate DSL, REST Assured, OWASP ZAP), and entry/exit criteria
- Defines all test execution commands, artifact formats, metric formulas, and report schemas that DevOps will wire into CI/CD

**Model routing rationale:** Strategy, planning, and tradeoff decisions require the strongest reasoning model. This is the quality-critical phase -- the plan shapes everything downstream.

---

### 3. QA-Generator+Review Agent (`agents/qa/qa-generator-review-agent.md`)

| Property | Value |
|----------|-------|
| **Model** | Cheap (Haiku 4.5 / GPT-4o-mini) |
| **Role** | Test scenario design + code generation + quality review |
| **Access** | Read repository (to verify selectors/imports exist) |
| **Input** | Approved test plan + coverage matrix |
| **Output** | `test-scenarios` + `test-code` + `qa-review-report` |

**Responsibilities (mapped from qa-skills):**
- `ai-test-generation` Steps 4-6 -- design scenarios from coverage matrix rows, define oracles (UI state / data / negative / side effect), generate test code with traceability comments
- `api-testing` -- REST/GraphQL test patterns: CRUD lifecycle, auth flows, error responses, response headers, pagination, schema validation (Zod 4/AJV), performance assertions
- `ai-qa-review` -- review generated test quality across 6 dimensions: readability, reliability, diagnostic value, design, AI-generated smells, coverage gaps
- `test-data-management` -- factories, fixtures, synthetic data, cleanup
- Mechanical verification -- resolve imports (`tsc --noEmit`), grep selectors/endpoints against codebase, run suite once to catch hallucinated APIs
- Output: test suites (Karate DSL, REST Assured, OWASP ZAP configs) + review report (severity per file, traceability verification, hallucination check results)

**Model routing rationale:** Generation and review are mechanical once the plan and matrix exist. A cheap model handles the translation to code. The review pass catches AI-generated smells (hallucinated APIs, weak assertions) before they reach CI.

---

### 4. QA-Critic Agent (existing, updated)

| Property | Value |
|----------|-------|
| **Model** | Cheap (reviews are mechanical checks) |
| **Role** | Adversarial plan review |
| **Input** | QA-Planner's test plan + strategy |
| **Output** | Approve / Reject with feedback |

**Responsibilities:**
- Prevent "happy path" bias -- demand malicious payloads, malformed API payloads, edge cases
- Verify NFR coverage (DAST, performance, load boundaries) in the plan
- Reject any plan that includes UI testing behavior
- Reject any plan that describes self-executing or self-retrying test logic

The critic remains lightweight: it checks for plan completeness and anti-patterns, not plan correctness (that is the expensive planner's job during debate).

---

### 5. DevOps Agent (existing, updated)

| Property | Value |
|----------|-------|
| **Model** | Cheap |
| **Role** | CI/CD pipeline plumbing |
| **Access** | Full repository (read/write) |
| **Input** | Test suites, qa-review-report, QA-defined execution commands and schemas |
| **Output** | `cicd-pipeline` + `cicd-run-summary.json` |

**Responsibilities:**
- Takes the exact execution commands, coverage thresholds, artifact formats, and report schemas defined by QA and wires them into CI/CD workflow YAML
- Creates docker-compose / environment provisioning per QA's environment requirements
- Uploads workflow artifacts (JUnit XML, HTML reports, traces, coverage) per QA-defined formats
- Collects raw pipeline data (pass/fail counts, duration, coverage %, flakiness %) and exports it in the QA-defined `cicd-run-summary.json` schema
- Creates quarantine job for `@flaky`-tagged tests per QA-defined quarantine criteria
- Reports infrastructure failures only; does NOT retry test assertion failures

---

## Workflow Integration

### Modified `development.yaml` Steps

```yaml
# PHASE 1: QA Context + Risk (cheap) -- runs in parallel with coding fanout
- id: qa-context-risk
  type: delegate
  description: QA gathers project context and builds risk matrix
  actor: qa-context-risk-agent
  input: [task-breakdown, srs]
  output: [qa-project-context, risk-matrix]

# PHASE 2: QA Planning (expensive) -- debated with critic
- id: qa-planning
  type: delegate
  description: QA Planner creates test strategy + sprint plan + coverage matrix
  actor: qa-planner-agent
  input: [qa-project-context, risk-matrix, implementation-plan]
  output: draft-qa-plan

- id: qa-debate
  type: debate
  description: QA Critic reviews plan for gaps, happy-path bias, NFR coverage
  actor: qa-planner-agent
  critic: qa-critic-agent
  artifact: draft-qa-plan
  max_turn: 3
  on_approved: qa-generate-review

# PHASE 3: QA Generate + Review (cheap) -- produces test suites
- id: qa-generate-review
  type: delegate
  description: QA generates test code from approved plan and reviews quality
  actor: qa-generator-review-agent
  input: [approved-qa-plan, approved-implementation-plan]
  output: [test-suites, qa-review-report]
  max_turn: 3

# PHASE 4: DevOps CI/CD (existing, updated)
- id: cicd-setup
  type: delegate
  description: DevOps wires QA-defined commands/metrics/reports into CI/CD pipeline
  actor: devops-agent
  input: [test-suites, qa-review-report, qa-defined-schemas]
  output: cicd-pipeline
```

### Removed Steps
- `qa-plan` worker in `worker-plans` fanout -- replaced by `qa-context-risk` + `qa-planning` sequential pipeline
- `qa-debate` on `qa-implementation-plan` -- replaced by debate on `draft-qa-plan`
- `qa-agent` actor in `implementation-execution` -- QA no longer participates in execution; separated into its own pipeline

---

## Data Contracts

### qa-context-risk-agent output: `qa-project-context.md`

```yaml
tech_stack:
  language: Python 3
  framework: FastAPI
  test_frameworks: [pytest, Karate DSL, REST Assured]
  security_tools: OWASP ZAP

ci_cd:
  platform: GitHub Actions
  pipeline_duration_target: "15min"
  artifact_storage: GitHub Artifacts

environments:
  local: Docker Compose (PostgreSQL, Redis)
  ci: Ephemeral containers
  staging: Shared (production-like, anonymized data)

quality_goals:
  coverage_target: {lines: 80, branches: 70}
  flakiness_target: "<2%"
  mttr_target: "<4h P0, <24h P1"

team_maturity: growing
```

### qa-context-risk-agent output: `risk-matrix`

```yaml
features:
  - name: "Payment processing"
    impact: 5          # Catastrophic
    probability: 3     # Possible
    score: 15          # CRITICAL
    failure_modes:
      - trigger: "Race condition between payment callback and order write"
        blast_radius: "Individual users; money charged but no order"
        detection_method: "Reconciliation job (hourly)"
        current_mitigation: "Idempotency key on payment"
        gap: "No automated test for the race condition"
    required_coverage:
      unit: "90%+ branch"
      integration: "All service boundaries"
      e2e: "Full user journey + error paths"

  - name: "User authentication"
    impact: 5
    probability: 2
    score: 10          # HIGH
    failure_modes:
      - trigger: "Token validation bypass"
        blast_radius: "All users; unauthorized access"
        detection_method: "Security scan (OWASP ZAP)"
        current_mitigation: "JWT signature verification"
        gap: "No automated DAST scan"
    required_coverage:
      unit: "80%+ branch"
      integration: "Key interactions"
      security: "OWASP ZAP scan"
```

### qa-planner-agent output: `test-strategy`

```yaml
scope:
  in:
    - Backend API services
    - REST endpoints
    - Data models and business logic
    - Security boundaries
  out:
    - UI/E2E (future extension)
    - Visual regression (future extension)
    - Performance testing (future extension)

pyramid_target:
  unit: 70
  integration: 20
  e2e: 5
  api: 5

entry_criteria:
  - Code complete on staging
  - Existing suite green
  - Test data seeded

exit_criteria:
  - 90%+ of HIGH and CRITICAL risk covered
  - No open P0/P1 defects
  - No unexplained GAP rows in coverage matrix
```

### qa-planner-agent output: `test-plan`

```yaml
sprint: "Sprint 12"
features:
  - name: "Order cancellation"
    risk_score: 15
    scenarios:
      - id: SC-001
        description: "Cancel order before shipping"
        category: happy_path
        priority: P0
        gherkin: |
          Given an order in "confirmed" status
          When the user cancels the order
          Then the order status is "cancelled"
          And a refund is initiated
        oracle:
          data: "GET /api/orders/{id} returns status=cancelled"
          side_effect: "Refund webhook dispatched"

  - name: "Concurrent cancellation"
    risk_score: 15
    scenarios:
      - id: SC-004
        description: "Two users cancel the same order simultaneously"
        category: concurrency
        priority: P1
        gherkin: |
          Given an order in "confirmed" status
          When two users cancel the same order simultaneously
          Then exactly one cancellation succeeds
          And the other receives a conflict error

buffer: "30%"
allocated_capacity: "70%"
```

### qa-planner-agent output: `coverage-matrix`

```yaml
requirements:
  - req: "REQ-CANCEL-1"
    description: "User can cancel an unshipped order"
    scenarios: [SC-001, SC-002, SC-003]
    status: covered

  - req: "REQ-CANCEL-2"
    description: "Partial order cancellation"
    scenarios: []
    status: GAP
    gap_decision: "Defer to next sprint (low-risk edge case)"

  - req: "REQ-CONC-1"
    description: "Concurrent cancellation handling"
    scenarios: [SC-004]
    status: covered
```

### qa-planner-agent output: `test-execution-schema`

QA defines the exact execution commands and output format:

```yaml
execution_commands:
  unit:
    command: "pytest tests/unit/ --tb=short --junitxml=test-results/unit.xml"
    timeout: "2m"
  api:
    command: "karate tests/api/ --output test-results/karate-reports"
    timeout: "5m"
  security:
    command: "zap-cli quick-scan --self-contained -r html -o test-results/zap-report.html"
    schedule: "weekly"
    severity_threshold: "medium"

artifact_formats:
  unit: "JUnit XML"
  api: "Karate HTML + JUnit XML"
  security: "OWASP ZAP HTML"
  coverage: "coverage-summary.json (lines, branches, functions)"

metric_formulas:
  flakiness_rate: "flaky_count / total_test_count * 100"
  defect_escape_rate: "prod_defects / (prod_defects + qa_defects) * 100"
  coverage_trend: "current_coverage - previous_coverage"

report_schemas:
  cicd_run_summary:
    run_id: "string"
    duration_seconds: "number"
    parallel_shards: "number"
    parallel_efficiency: "number"
    results:
      unit: {pass: "number", fail: "number", skip: "number", duration: "string"}
      api: {pass: "number", fail: "number", skip: "number", duration: "string"}
    coverage:
      lines: "percentage"
      branches: "percentage"
      functions: "percentage"
    flakiness:
      quarantined: "number"
      new_this_run: "number"
    artifacts:
      - "string (path)"
    alerts: "string"
```

### qa-generator-review-agent output: `test-code`

Test suites generated from the approved plan:

```yaml
test_suites:
  - type: karate
    path: "tests/api/order-cancellation.feature"
    scenarios: 3
    status: generated
    traceability:
      SC-001: "tests/api/order-cancellation.feature:1"
      SC-002: "tests/api/order-cancellation.feature:20"
      SC-003: "tests/api/order-cancellation.feature:45"

  - type: owasp_zap
    path: "tests/security/order-cancellation-zap.yaml"
    status: generated
    severity_threshold: "medium"
```

### qa-generator-review-agent output: `qa-review-report`

```yaml
files_reviewed:
  - file: "tests/api/order-cancellation.feature"
    smell_dimensions:
      readability: pass
      reliability: pass
      diagnostic: pass
      design: pass
      ai_generated:
        hallucinated_apis: none
        imports_resolve: true
        selector_verification: "N/A (API tests)"
      coverage:
        happy_path: [SC-001, SC-002]
        negative: [SC-003]
        boundary: [SC-004]
        gap: "Missing: concurrent cancellation by two users"
    severity: low
    action: "KEEP -- add concurrent test in next sprint"

suite_run:
  pass: 7
  fail: 1
  skip: 0

mutation_score: 0.72

flakiness_check:
  runs: 3
  flaky: 0
```

### devops-agent output: `cicd-run-summary.json`

DevOps collects raw data and exports it in QA-defined schema:

```json
{
  "run_id": "ci-12345",
  "workflow": ".github/workflows/test.yml",
  "duration_seconds": 187,
  "parallel_shards": 4,
  "parallel_efficiency": 3.7,
  "results": {
    "unit": { "pass": 142, "fail": 0, "skip": 0, "duration": "12s" },
    "api": { "pass": 7, "fail": 0, "skip": 0, "duration": "28s" },
    "security": { "pass": 1, "fail": 0, "skip": 0, "duration": "45s" }
  },
  "coverage": {
    "lines": 78.3,
    "branches": 65.1,
    "functions": 82.0
  },
  "flakiness": {
    "quarantined": 2,
    "new_this_run": 0
  },
  "artifacts": [
    "playwright-report/index.html",
    "coverage/lcov-report/index.html",
    "test-results/junit.xml"
  ],
  "alerts": "No P0/P1 failures"
}
```

### HITL Dashboard

Human-in-the-loop receives a consolidated view:

| Artifact | Source | Content |
|----------|--------|---------|
| Risk matrix | QA-Context+Risk | Feature-level risk scores, failure modes, required coverage |
| Test strategy + plan | QA-Planner | What is tested, depth, entry/exit criteria |
| Coverage matrix | QA-Planner | Requirement-to-scenario mapping, gaps |
| QA review report | QA-Generator+Review | Test quality, smells, traceability, mutation score |
| CI run summary | DevOps | Pass/fail, coverage, flakiness, artifacts |
| Security scan | DevOps | OWASP ZAP results, severity distribution |

---

## Error Handling

| Error | Detected By | Handler |
|-------|-------------|---------|
| Missing project context | QA-Context+Risk | Creates it from scratch; surfaces ambiguities |
| Unresolved risk ambiguity | QA-Planner | Flags in plan for HITL; does not silently pick |
| Hallucinated API/endpoint/selector | QA-Generator+Review | `tsc --noEmit` + grep verification catches before CI |
| Weak assertions (toBeTruthy, etc.) | QA-Generator+Review | ai-qa-review smell pass flags them; mutation score confirms |
| Test assertion failure (TDD behavior) | DevOps CI | DevOps reports to PM; does NOT retry or fix |
| Infrastructure failure | DevOps CI | DevOps retries on infra; reports to PM if persistent |
| Flaky test | DevOps Nightly | Quarantine job (`--grep @flaky`); non-blocking |
| Plan rejected by critic | QA-Planner + QA-Critic | Re-debate up to max_turn; if max, escalate to HITL |

---

## Cost Model

| Agent | Model Tier | Relative Cost | When Active |
|-------|-----------|---------------|-------------|
| QA-Context+Risk | Cheap | 0.1x | Once per task (fanout) |
| QA-Planner | Expensive | 1.0x | Once per task + up to 3 debate turns |
| QA-Critic | Cheap | 0.1x | Only during debate (reviews plan) |
| QA-Generator+Review | Cheap | 0.1x | Once per task |
| DevOps | Cheap | 0.1x | Once per task |
| **Total QA** | | **~1.4x** | |

**Comparison:** Old `qa-agent` used expensive model for 2 phases + debate (~2-3x expensive-model-equivalent). **Savings: ~50% reduction** while adding risk analysis, coverage matrix, and quality review.

---

## Migration Path

1. Create `agents/qa/qa-context-risk-agent.md`
2. Create `agents/qa/qa-planner-agent.md`
3. Create `agents/qa/qa-generator-review-agent.md`
4. Update `agents/qa/qa-critic-agent.md` to review planner output (not executor)
5. Update `agents/devops/devops-agent.md` to wire QA-defined commands/schemas
6. Update `workflow/development.yaml` -- replace `qa-plan` fanout + `qa-debate` + execution with 4-phase pipeline
7. Update `skills/components/qa/skills.yaml` to register new agent skills
8. Deprecate old `qa-agent.md` (rename to `archive/qa-agent-deprecated.md`)

---

## Extension Hooks (Future)

| Extension | Agent to add | Model | Phase |
|-----------|-------------|-------|-------|
| UI/E2E testing | qa-e2e-agent | Cheap | After generator-review |
| Visual regression | devops-agent (visual gate) | Cheap | CI nightly |
| Performance testing | devops-agent (k6/Lighthouse) | Cheap | CI pre-release |
| Accessibility testing | devops-agent (axe-core) | Cheap | CI nightly |
| Security scanning | devops-agent (OWASP ZAP) | Cheap | CI scheduled |
| QA metrics dashboard | qa-metrics-agent | Cheap | Post-release reporting |

---

## Related Documents

- [Three-Agent Coding Pipeline Design](2026-06-10-three-agent-coding-pipeline-design.md)
- [Skills Module Sidecar Injection](2026-06-13-skills-module-sidecar-injection-design.md)
- [petrkindlmann/qa-skills](https://github.com/petrkindlmann/qa-skills) -- upstream skill repository
- Current `agents/qa/qa-agent.md`, `agents/qa/qa-critic-agent.md`, `agents/devops/devops-agent.md`

# Bootstrap Help Text Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update Makefile help comments and add inline examples to document multi-repo mode for bootstrap and bootstrap-gitnexus targets.

**Architecture:** Pure documentation changes (comments only) — Makefile target behavior unchanged.

**Tech Stack:** Makefile syntax, shell comments

---

## Task 1: Add inline examples comment block

**Files:**
- Modify: `/home/dinhhuy/Workspace/pet-project/agentic-sdlc-system/Makefile:27-28`
- Test: N/A (comments only)

Add examples comment block after `INCLUDE_GITNEXUS_ANALYZE ?= 0` on line 27.

- [ ] **Step 1: Verify current content at line 27-28**

Current lines (line 27 is `INCLUDE_GITNEXUS_ANALYZE ?= 0`, line 28 is blank, line 29 is `bootstrap:` target):
```makefile
INCLUDE_GITNEXUS_ANALYZE ?= 0

bootstrap: ## Bootstrap wiki, skills, GitNexus install, agents, and workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [RUNTIME_ID=my-id] [WORKFLOW=workflow.yaml] [INCLUDE_GITNEXUS_ANALYZE=0|1])
```

- [ ] **Step 2: Insert examples comment block**

Edit `Makefile`, find exact string:
```
INCLUDE_GITNEXUS_ANALYZE ?= 0

bootstrap:
```

Replace with:
```
INCLUDE_GITNEXUS_ANALYZE ?= 0

# Examples:
#   make bootstrap                                              # wiki + skills + agents + workflow (no GitNexus analysis)
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1                   # + monorepo (prompts for GITNEXUS_REPO)
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=monorepo GITNEXUS_REPO=org/repo
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=multi-repo GITNEXUS_REPOS="org/a org/b" GROUP_NAME=my-group
#   make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo
#   make bootstrap-gitnexus MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group

bootstrap:
```

- [ ] **Step 3: Verify `make help` still works**

Run:
```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system && make help
```

Expected: `bootstrap` and `bootstrap-gitnexus` still appear. Comment block not in output (correct; `grep` only matches lines with `target: ##`).

- [ ] **Step 4: Commit**

```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system
git add Makefile
git commit -m "docs: add inline examples for bootstrap multi-repo mode"
```

---

## Task 2: Update `bootstrap` target help text

**Files:**
- Modify: `/home/dinhhuy/Workspace/pet-project/agentic-sdlc-system/Makefile:29`

- [ ] **Step 1: Verify current `bootstrap` target line 29**

Current:
```makefile
bootstrap: ## Bootstrap wiki, skills, GitNexus install, agents, and workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [RUNTIME_ID=my-id] [WORKFLOW=workflow.yaml] [INCLUDE_GITNEXUS_ANALYZE=0|1])
```

- [ ] **Step 2: Update the `##` help string**

Find exact string:
```
bootstrap: ## Bootstrap wiki, skills, GitNexus install, agents, and workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [RUNTIME_ID=my-id] [WORKFLOW=workflow.yaml] [INCLUDE_GITNEXUS_ANALYZE=0|1])
```

Replace with:
```
bootstrap: ## Bootstrap wiki, skills, agents, workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [WORKFLOW=...] [INCLUDE_GITNEXUS_ANALYZE=0|1] [MODE=monorepo|multi-repo] [GITNEXUS_REPOS="org/a org/b"] [GROUP_NAME=my-group])
```

Changes made:
- Removed "GitNexus install" from description (optional, secondary)
- Removed "RUNTIME_ID=my-id" from explicit usage string (still works via env; rare use case)
- Shortened "workflow.yaml" to "..." for brevity
- Added: `MODE=monorepo|multi-repo`, `GITNEXUS_REPOS="org/a org/b"`, `GROUP_NAME=my-group`

- [ ] **Step 3: Run `make help` to verify**

Run:
```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system && make help
```

Expected: `bootstrap` line shows new help text including `MODE=monorepo|multi-repo`, `GITNEXUS_REPOS`, `GROUP_NAME`.

- [ ] **Step 4: Commit**

```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system
git add Makefile
git commit -m "docs: update bootstrap help to document multi-repo variables"
```

---

## Task 3: Update `bootstrap-gitnexus` target help text

**Files:**
- Modify: `/home/dinhhuy/Workspace/pet-project/agentic-sdlc-system/Makefile:62`

- [ ] **Step 1: Verify current `bootstrap-gitnexus` target line 62**

Current:
```makefile
bootstrap-gitnexus: ## Bootstrap GitNexus runtime and analyze repository(ies) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo)
```

- [ ] **Step 2: Update the `##` help string**

Find exact string:
```
bootstrap-gitnexus: ## Bootstrap GitNexus runtime and analyze repository(ies) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo)
```

Replace with:
```
bootstrap-gitnexus: ## Bootstrap GitNexus runtime and analyze repo(s) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo | MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group)
```

Changes made:
- Shortened "repository(ies)" to "repo(s)"
- Added `|` separator to show mutually exclusive modes
- Added multi-repo usage: `MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group`

- [ ] **Step 3: Run `make help` to verify**

Run:
```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system && make help
```

Expected: `bootstrap-gitnexus` line shows both monorepo and multi-repo usage patterns.

- [ ] **Step 4: Commit**

```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system
git add Makefile
git commit -m "docs: update bootstrap-gitnexus help to show multi-repo mode"
```

---

## Task 4: Final verification

**Files:**
- Test: None

- [ ] **Step 1: Run final `make help` check**

```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system && make help
```

Expected output contains these lines (exact text):
- `bootstrap         Bootstrap wiki, skills, agents, workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [WORKFLOW=...] [INCLUDE_GITNEXUS_ANALYZE=0|1] [MODE=monorepo|multi-repo] [GITNEXUS_REPOS="org/a org/b"] [GROUP_NAME=my-group])`
- `bootstrap-gitnexus Bootstrap GitNexus runtime and analyze repo(s) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo | MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group)`

- [ ] **Step 2: Verify git log shows 3 commits**

```bash
cd /home/dinhhuy/Workspace/pet-project/agentic-sdlc-system && git log --oneline -3
```

Expected: Three commits matching task 1, task 2, task 3.

---

## Plan Self-Review

**1. Spec coverage:**
- Task 1 implements: Add inline examples block (spec section 3)
- Task 2 implements: Update bootstrap help line (spec section 1)
- Task 3 implements: Update bootstrap-gitnexus help line (spec section 2)
- Spec section 4 (README) correctly marked "no changes needed"

**2. Placeholder scan:**
- No TBD, no TODO in plan
- All edit strings show exact before/after
- All commands are explicit with expected behavior described

**3. Type consistency:**
- Variable names match Makefile exactly: `MODE`, `GITNEXUS_REPOS`, `REPOS`, `GROUP_NAME`, `INCLUDE_GITNEXUS_ANALYZE`
- All steps reference same files and line numbers

**4. Scope check:**
- All changes are comments only; recipe behavior unchanged
- Correctly identifies README needs no update
- Tests: only `make help` verification (appropriate for doc changes)

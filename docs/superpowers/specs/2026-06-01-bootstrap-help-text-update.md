---
title: Bootstrap Help Text Update
description: Update Makefile help comments and inline examples to document multi-repo mode for bootstrap and bootstrap-gitnexus targets
date: 2026-06-01
status: approved
---

# Bootstrap Help Text Update

## Problem

Both `bootstrap` and `bootstrap-gitnexus` targets support multi-repo mode via `MODE=multi-repo`, but the Makefile `##` help comments and `make help` output don't document:

- The `MODE` variable
- `GITNEXUS_REPOS` (for `bootstrap` multi-repo path)
- `REPOS` and `GROUP_NAME` (for `bootstrap-gitnexus` multi-repo path)

Users discover multi-repo mode only by reading the Makefile recipe internals or README — not from `make help`.

## Goal

Make `make help` output self-documenting for all bootstrap modes, and add inline Makefile examples as reference for users editing the Makefile directly.

## Changes

### 1. Update `bootstrap` help line (Makefile line 29)

**Before:**
```
bootstrap: ## Bootstrap wiki, skills, GitNexus install, agents, and workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [RUNTIME_ID=my-id] [WORKFLOW=workflow.yaml] [INCLUDE_GITNEXUS_ANALYZE=0|1])
```

**After:**
```
bootstrap: ## Bootstrap wiki, skills, agents, workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [WORKFLOW=...] [INCLUDE_GITNEXUS_ANALYZE=0|1] [MODE=monorepo|multi-repo] [GITNEXUS_REPOS="org/a org/b"] [GROUP_NAME=my-group])
```

Changes:
- Shortened description (removed "GitNexus install" since that's optional and secondary)
- Removed `RUNTIME_ID` from help (rare use case; still works via env)
- Added `MODE`, `GITNEXUS_REPOS`, `GROUP_NAME` to the usage string

### 2. Update `bootstrap-gitnexus` help line (Makefile line 62)

**Before:**
```
bootstrap-gitnexus: ## Bootstrap GitNexus runtime and analyze repository(ies) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo)
```

**After:**
```
bootstrap-gitnexus: ## Bootstrap GitNexus runtime and analyze repo(s) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo | MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group)
```

Changes:
- Added `|` separator to show the two modes are mutually exclusive
- Shows both monorepo and multi-repo invocations in one line

### 3. Add inline examples block (Makefile, after line 27)

Add a comment block showing concrete invocations:

```makefile
# Examples:
#   make bootstrap                                              # wiki + skills + agents + workflow (no GitNexus analysis)
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1                   # + monorepo (prompts for GITNEXUS_REPO)
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=monorepo GITNEXUS_REPO=org/repo
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=multi-repo GITNEXUS_REPOS="org/a org/b" GROUP_NAME=my-group
#   make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo
#   make bootstrap-gitnexus MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group
```

### 4. README.md — No changes needed

README already documents:
- Full bootstrap multi-repo example (line 71)
- GitNexus multi-repo example (lines 91-107)

Both are correct and complete.

## Scope

- Makefile only — help text comments and inline example comments
- No code logic changes
- No new targets, no new CLI arguments
- No README changes (already documented)

## Testing

- Run `make help` and verify the updated help text appears correctly
- Verify `make bootstrap` and `make bootstrap-gitnexus` behavior unchanged (comments only)

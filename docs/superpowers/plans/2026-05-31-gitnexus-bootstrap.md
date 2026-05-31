# GitNexus Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated GitNexus bootstrap command that installs GitNexus and runs monorepo or multi-repo analysis flows.

**Architecture:** Introduce a focused bootstrap module for GitNexus command execution, keep CLI wiring thin, and reuse the existing entrypoint pattern used by the Obsidian bootstrap. The bootstrap module will own repository normalization, mode selection, command construction, and external process execution so the CLI layer only parses arguments and delegates.

**Tech Stack:** Python 3.12, `argparse`, `subprocess`, `pathlib`, `unittest`

---

### Task 1: Add bootstrap tests for GitNexus execution

**Files:**
- Create: `tests/test_bootstrap_gitnexus.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from src.bootstrap_gitnexus import normalize_repo_input, build_gitnexus_install_command, build_analyze_command


class TestBootstrapGitNexus(unittest.TestCase):
    def test_normalize_repo_input_accepts_slug(self):
        self.assertEqual(normalize_repo_input("org/repo"), "org/repo")

    def test_normalize_repo_input_accepts_https_url(self):
        self.assertEqual(
            normalize_repo_input("https://github.com/org/repo.git"),
            "org/repo",
        )

    def test_build_gitnexus_install_command(self):
        self.assertEqual(build_gitnexus_install_command(), ["npm", "install", "-g", "gitnexus"])

    def test_build_analyze_command_single_repo(self):
        self.assertEqual(build_analyze_command("org/repo"), ["npx", "gitnexus", "analyze", "org/repo"])
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `python -m unittest discover -s tests -p 'test_bootstrap_gitnexus.py'`
Expected: FAIL because `src.bootstrap_gitnexus` does not exist yet.

- [ ] **Step 3: Add the test file scaffolding only**

Create `tests/test_bootstrap_gitnexus.py` with the code above and no implementation changes yet.

- [ ] **Step 4: Run the test again**

Run: `python -m unittest discover -s tests -p 'test_bootstrap_gitnexus.py'`
Expected: FAIL with an import error until the bootstrap module is implemented.

- [ ] **Step 5: Commit the red-state test**

```bash
git add tests/test_bootstrap_gitnexus.py
git commit -m "test: add GitNexus bootstrap coverage"
```

### Task 2: Implement the GitNexus bootstrap module

**Files:**
- Create: `src/bootstrap_gitnexus.py`
- Modify: `src/adapters/cli/entrypoint.py`

- [ ] **Step 1: Implement the minimal bootstrap module**

```python
#!/usr/bin/env python3
"""Bootstrap GitNexus runtime integration for codebase knowledge analysis."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def normalize_repo_input(repo: str) -> str:
    value = repo.strip()
    if not value:
        raise ValueError("Repository cannot be empty")

    value = re.sub(r"\.git$", "", value)

    https_match = re.match(r"^https://github\.com/([^/]+)/([^/]+)$", value)
    ssh_match = re.match(r"^git@github\.com:([^/]+)/([^/]+)$", value)
    slug_match = re.match(r"^([^/\s]+)/([^/\s]+)$", value)

    if https_match:
        return f"{https_match.group(1)}/{https_match.group(2)}"
    if ssh_match:
        return f"{ssh_match.group(1)}/{ssh_match.group(2)}"
    if slug_match:
        return value

    raise ValueError("Unsupported repo format. Use owner/repo or a GitHub URL")


def build_gitnexus_install_command() -> list[str]:
    return ["npm", "install", "-g", "gitnexus"]


def build_analyze_command(repo: str) -> list[str]:
    return ["npx", "gitnexus", "analyze", repo]


def _run(command: list[str], cwd: str | None = None, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[dry-run] {' '.join(command)}")
        return

    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or "no output"
        raise RuntimeError(f"Command failed ({' '.join(command)}): {details}")


def run_bootstrap(args: argparse.Namespace) -> None:
    mode = args.mode
    repos = args.repos or []
    repo = args.repo

    if mode == "monorepo" and not repo:
        raise RuntimeError("--repo is required for monorepo mode")
    if mode == "multi-repo" and not repos:
        raise RuntimeError("--repos is required for multi-repo mode")

    _run(build_gitnexus_install_command(), dry_run=args.dry_run)

    if mode == "monorepo":
        resolved = normalize_repo_input(repo)
        _run(build_analyze_command(resolved), dry_run=args.dry_run)
        return

    group_name = args.group_name or "gitnexus-group"
    _run(["npx", "gitnexus", "group", "create", group_name], dry_run=args.dry_run)
    for repo_value in repos:
        resolved = normalize_repo_input(repo_value)
        _run(["npx", "gitnexus", "repo", "pull", resolved], dry_run=args.dry_run)
        _run(build_analyze_command(resolved), dry_run=args.dry_run)
        _run(["npx", "gitnexus", "group", "attach", group_name, resolved], dry_run=args.dry_run)
    _run(["npx", "gitnexus", "group", "sync", group_name], dry_run=args.dry_run)


def build_parser(subparsers) -> None:
    parser = subparsers.add_parser("bootstrap-gitnexus", help="bootstrap GitNexus runtime and analysis flow")
    parser.add_argument("--mode", choices=["monorepo", "multi-repo"], required=True, help="working mode")
    parser.add_argument("--repo", help="monorepo input (owner/repo or URL)")
    parser.add_argument("--repos", nargs="*", help="multi-repo inputs (owner/repo or URL)")
    parser.add_argument("--group-name", help="GitNexus group name for multi-repo mode")
    parser.add_argument("--dry-run", action="store_true", help="print actions without executing them")
    parser.set_defaults(func=run_bootstrap)
```

Update `src/adapters/cli/entrypoint.py` so the parser imports and registers `build_parser` from the new module, then add a `bootstrap-gitnexus` subcommand alongside the existing `bootstrap-wiki` command.

- [ ] **Step 2: Run the targeted tests to confirm the first implementation passes**

Run: `python -m unittest discover -s tests -p 'test_bootstrap_gitnexus.py'`
Expected: PASS.

- [ ] **Step 3: Run the CLI smoke test**

Run: `python -m src.cli bootstrap-gitnexus --help`
Expected: shows `--mode`, `--repo`, `--repos`, and `--group-name`.

- [ ] **Step 4: Commit the implementation**

```bash
git add src/bootstrap_gitnexus.py src/adapters/cli/entrypoint.py tests/test_bootstrap_gitnexus.py
git commit -m "feat: add GitNexus bootstrap command"
```

### Task 3: Verify existing bootstrap behavior stays intact

**Files:**
- Modify: none

- [ ] **Step 1: Run the existing bootstrap tests**

Run: `python -m unittest discover -s tests -p 'test_bootstrap_obsidian_wiki.py'`
Expected: PASS.

- [ ] **Step 2: Run the CLI test suite**

Run: `python -m unittest discover -s tests -p 'test_cli.py'`
Expected: PASS.

- [ ] **Step 3: Run the full test suite**

Run: `python -m unittest discover -s tests`
Expected: PASS.

- [ ] **Step 4: Commit the verification runbook note if needed**

If the implementation changes any operator-facing behavior, add a short note to the repo docs describing how to use `bootstrap-gitnexus` in monorepo and multi-repo mode.

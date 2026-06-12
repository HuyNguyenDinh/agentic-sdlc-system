# Bootstrap Skill Injection Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor bootstrap skill setup so local installation, Multica import, baseline assignment, and per-agent IaC skill bindings run through one coherent flow.

**Architecture:** Introduce a focused Multica skill service that owns skill discovery, create/update, ID resolution, and assignment. Keep `src.install_skills` for local `skills.txt` installation, make `src.bootstrap_multica_skills` a wrapper, and let `MulticaAdapter` optionally bind IaC-declared skills after agent publication.

**Tech Stack:** Python 3, standard library `unittest` and `unittest.mock`, `argparse`, `subprocess`, Makefile.

---

## File Structure

- Create: `src/core/services/multica_skill_service.py`
  - Owns local skill scanning, baseline filtering, Multica skill create/update, skill ID resolution, agent listing, single-agent assignment, all-agent assignment, and dry-run behavior.
- Modify: `src/bootstrap_multica_skills.py`
  - Keeps the existing module/CLI entrypoint but delegates to `MulticaSkillService`.
- Modify: `src/adapters/multica_adapter.py`
  - Accepts an optional skill service and applies IaC-declared skills after agent create/update.
- Modify: `src/adapters/cli/entrypoint.py`
  - Imports the service, wires `bootstrap-skills`, and reorders umbrella `bootstrap`.
- Modify: `Makefile`
  - Adds a `bootstrap-skills` target and includes it in `.PHONY`.
- Create: `tests/test_multica_skill_service.py`
  - Covers service scan/filter/create/update/resolve/assign/dry-run behavior.
- Modify: `tests/test_multica_adapter.py`
  - Covers per-agent skill assignment and failure behavior.
- Modify: `tests/test_cli.py`
  - Covers `bootstrap-skills` command wiring and umbrella bootstrap order.

---

### Task 1: Add Multica Skill Service Tests

**Files:**
- Create: `tests/test_multica_skill_service.py`
- Read: `src/bootstrap_multica_skills.py`

- [ ] **Step 1: Write failing tests for service behavior**

Create `tests/test_multica_skill_service.py` with this complete content:

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.core.services.multica_skill_service import MulticaSkillService


class TestMulticaSkillService(unittest.TestCase):
    def make_service(self, run_cmd=None, skills_dir=None, baseline_skills=None):
        return MulticaSkillService(
            skills_dir=skills_dir or Path("/missing/skills"),
            baseline_skills=baseline_skills or ["brainstorming", "writing-plans"],
            run_cmd=run_cmd or (lambda args, **kwargs: MagicMock(returncode=0, stdout="", stderr="")),
        )

    def test_get_local_skills_scans_skill_md_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            skills_dir = Path(tmp_dir)
            (skills_dir / "brainstorming").mkdir()
            (skills_dir / "brainstorming" / "SKILL.md").write_text("# Brainstorming\n", encoding="utf-8")
            (skills_dir / "no-skill-file").mkdir()

            service = self.make_service(skills_dir=skills_dir)

            self.assertEqual(
                service.get_local_skills(),
                {"brainstorming": skills_dir / "brainstorming" / "SKILL.md"},
            )

    def test_get_multica_skills_parses_table_output(self):
        def run_cmd(args, **kwargs):
            self.assertEqual(args, ["multica", "skill", "list"])
            return MagicMock(
                returncode=0,
                stdout="ID NAME DESCRIPTION\nskill-1 brainstorming Brainstorming\nskill-2 writing-plans Planning\n",
                stderr="",
            )

        service = self.make_service(run_cmd=run_cmd)

        self.assertEqual(
            service.get_multica_skills(),
            {"brainstorming": "skill-1", "writing-plans": "skill-2"},
        )

    def test_create_or_update_skill_updates_existing_skill(self):
        calls = []

        def run_cmd(args, **kwargs):
            calls.append(args)
            if args == ["multica", "skill", "list"]:
                return MagicMock(returncode=0, stdout="ID NAME\nskill-1 brainstorming\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_md = Path(tmp_dir) / "SKILL.md"
            skill_md.write_text("# Brainstorming\n", encoding="utf-8")
            service = self.make_service(run_cmd=run_cmd)

            skill_id = service.create_or_update_skill("brainstorming", skill_md)

        self.assertEqual(skill_id, "skill-1")
        self.assertIn(
            [
                "multica",
                "skill",
                "update",
                "skill-1",
                "--config",
                '{"name": "brainstorming"}',
                "--content-file",
                str(skill_md.resolve()),
            ],
            calls,
        )

    def test_create_or_update_skill_creates_missing_skill(self):
        calls = []

        def run_cmd(args, **kwargs):
            calls.append(args)
            if args == ["multica", "skill", "list"]:
                return MagicMock(returncode=0, stdout="ID NAME\n", stderr="")
            return MagicMock(returncode=0, stdout='{"id": "new-skill"}', stderr="")

        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_md = Path(tmp_dir) / "SKILL.md"
            skill_md.write_text("# Brainstorming\n", encoding="utf-8")
            service = self.make_service(run_cmd=run_cmd)

            skill_id = service.create_or_update_skill("brainstorming", skill_md)

        self.assertEqual(skill_id, "new-skill")
        self.assertIn(
            [
                "multica",
                "skill",
                "create",
                "--name",
                "brainstorming",
                "--description",
                "Brainstorming",
                "--content-file",
                str(skill_md.resolve()),
            ],
            calls,
        )

    def test_sync_baseline_skills_filters_to_baseline(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            skills_dir = Path(tmp_dir)
            for name in ["brainstorming", "personal-skill"]:
                (skills_dir / name).mkdir()
                (skills_dir / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

            def run_cmd(args, **kwargs):
                if args == ["multica", "skill", "list"]:
                    return MagicMock(returncode=0, stdout="ID NAME\n", stderr="")
                return MagicMock(returncode=0, stdout='{"id": "skill-brainstorming"}', stderr="")

            service = self.make_service(
                run_cmd=run_cmd,
                skills_dir=skills_dir,
                baseline_skills=["brainstorming"],
            )

            self.assertEqual(service.sync_baseline_skills(), ["skill-brainstorming"])

    def test_resolve_skill_ids_returns_missing_names(self):
        service = self.make_service(
            run_cmd=lambda args, **kwargs: MagicMock(
                returncode=0,
                stdout="ID NAME\nskill-1 brainstorming\n",
                stderr="",
            )
        )

        resolved, missing = service.resolve_skill_ids(["brainstorming", "missing"])

        self.assertEqual(resolved, ["skill-1"])
        self.assertEqual(missing, ["missing"])

    def test_assign_skills_to_agent_uses_comma_separated_ids(self):
        calls = []

        def run_cmd(args, **kwargs):
            calls.append(args)
            return MagicMock(returncode=0, stdout="", stderr="")

        service = self.make_service(run_cmd=run_cmd)

        self.assertTrue(service.assign_skills_to_agent("agent-1", "coder", ["skill-1", "skill-2"]))
        self.assertEqual(
            calls,
            [["multica", "agent", "skills", "set", "agent-1", "--skill-ids", "skill-1,skill-2"]],
        )

    def test_assign_skills_to_all_agents_fails_when_one_agent_fails(self):
        def run_cmd(args, **kwargs):
            if args == ["multica", "agent", "list"]:
                return MagicMock(returncode=0, stdout="ID NAME\nagent-1 coder\nagent-2 planner\n", stderr="")
            if args[:5] == ["multica", "agent", "skills", "set", "agent-2"]:
                return MagicMock(returncode=1, stdout="", stderr="assign failed")
            return MagicMock(returncode=0, stdout="", stderr="")

        service = self.make_service(run_cmd=run_cmd)

        self.assertFalse(service.assign_skills_to_all_agents(["skill-1"]))

    def test_dry_run_does_not_execute_mutation_commands(self):
        calls = []

        def run_cmd(args, **kwargs):
            calls.append(args)
            return MagicMock(returncode=0, stdout="ID NAME\nskill-1 brainstorming\n", stderr="")

        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_md = Path(tmp_dir) / "SKILL.md"
            skill_md.write_text("# Brainstorming\n", encoding="utf-8")
            service = self.make_service(run_cmd=run_cmd)

            skill_id = service.create_or_update_skill("brainstorming", skill_md, dry_run=True)
            assigned = service.assign_skills_to_agent("agent-1", "coder", ["skill-1"], dry_run=True)

        self.assertEqual(skill_id, "skill-1")
        self.assertTrue(assigned)
        self.assertEqual(calls, [["multica", "skill", "list"]])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests to verify they fail because the service does not exist**

Run:

```bash
python -m unittest tests.test_multica_skill_service
```

Expected: `ModuleNotFoundError: No module named 'src.core.services.multica_skill_service'`.

- [ ] **Step 3: Commit the failing tests**

Run:

```bash
git add tests/test_multica_skill_service.py
git commit -m "test: specify multica skill service behavior"
```

---

### Task 2: Implement Multica Skill Service

**Files:**
- Create: `src/core/services/multica_skill_service.py`
- Modify: `src/bootstrap_multica_skills.py`
- Test: `tests/test_multica_skill_service.py`

- [ ] **Step 1: Add the service implementation**

Create `src/core/services/multica_skill_service.py` with this complete content:

```python
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional


DEFAULT_SKILLS_DIR = Path.home() / ".agents" / "skills"

DEFAULT_BASELINE_SKILLS = [
    "llm-wiki",
    "obsidian",
    "obsidian-wiki-ingest",
    "wiki-agent",
    "wiki-capture",
    "wiki-context-pack",
    "wiki-dashboard",
    "wiki-dedup",
    "wiki-digest",
    "wiki-export",
    "wiki-history-ingest",
    "wiki-import",
    "wiki-ingest",
    "wiki-lint",
    "wiki-query",
    "wiki-quick-chat-capture",
    "wiki-rebuild",
    "wiki-research",
    "wiki-setup",
    "wiki-stage-commit",
    "wiki-status",
    "wiki-switch",
    "wiki-synthesize",
    "wiki-update",
    "brainstorming",
    "dispatching-parallel-agents",
    "executing-plans",
    "finishing-a-development-branch",
    "multica-collaboration",
    "prd",
    "receiving-code-review",
    "requesting-code-review",
    "subagent-driven-development",
    "systematic-debugging",
    "test-driven-development",
    "using-git-worktrees",
    "using-superpowers",
    "verification-before-completion",
    "writing-plans",
    "writing-skills",
    "todoist",
    "cross-linker",
    "tag-taxonomy",
    "graph-colorize",
    "data-ingest",
    "ingest-url",
    "daily-update",
    "memory-bridge",
    "arxiv",
    "blogwatcher",
    "polymarket",
    "gif-search",
    "heartmula",
    "songsee",
    "youtube-content",
    "github-auth",
    "github-code-review",
    "github-issues",
    "github-pr-workflow",
    "github-repo-management",
    "codebase-inspection",
]


RunCommand = Callable[..., subprocess.CompletedProcess]


def run_multica_command(args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, check=False, timeout=timeout)
    except FileNotFoundError:
        res = subprocess.CompletedProcess(args, returncode=127)
        res.stderr = "multica: command not found"
        return res
    except subprocess.TimeoutExpired:
        res = subprocess.CompletedProcess(args, returncode=124)
        res.stderr = "Command timed out"
        return res


class MulticaSkillService:
    def __init__(
        self,
        *,
        skills_dir: Path = DEFAULT_SKILLS_DIR,
        baseline_skills: Optional[list[str]] = None,
        run_cmd: RunCommand = run_multica_command,
    ):
        self.skills_dir = Path(skills_dir)
        self.baseline_skills = list(dict.fromkeys(baseline_skills or DEFAULT_BASELINE_SKILLS))
        self._run_cmd = run_cmd

    def get_local_skills(self) -> dict[str, Path]:
        skills: dict[str, Path] = {}
        if not self.skills_dir.is_dir():
            return skills
        for entry in sorted(self.skills_dir.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if skill_md.is_file():
                skills[entry.name] = skill_md
        return skills

    def get_multica_skills(self) -> dict[str, str]:
        res = self._run_cmd(["multica", "skill", "list"])
        if res.returncode != 0:
            return {}
        skills: dict[str, str] = {}
        lines = res.stdout.strip().splitlines()
        if len(lines) <= 1:
            return skills
        for line in lines[1:]:
            parts = line.split(maxsplit=3)
            if len(parts) >= 2:
                skills[parts[1]] = parts[0]
        return skills

    def create_or_update_skill(self, name: str, skill_md_path: Path, *, dry_run: bool = False) -> Optional[str]:
        existing = self.get_multica_skills()
        desc = self._description_from_skill(skill_md_path, name)

        if name in existing:
            skill_id = existing[name]
            if dry_run:
                print(f"  [dry-run] multica skill update {skill_id} --name {name}")
                return skill_id

            res = self._run_cmd(
                [
                    "multica",
                    "skill",
                    "update",
                    skill_id,
                    "--config",
                    json.dumps({"name": name}),
                    "--content-file",
                    str(skill_md_path.resolve()),
                ]
            )
            if res.returncode != 0:
                print(f"  x Failed to update skill '{name}': {res.stderr.strip()}", file=sys.stderr)
                return None
            print(f"  OK Updated skill '{name}' ({skill_id})")
            return skill_id

        if dry_run:
            print(f"  [dry-run] multica skill create --name {name} --description {desc!r} --content-file {skill_md_path.resolve()}")
            return None

        res = self._run_cmd(
            [
                "multica",
                "skill",
                "create",
                "--name",
                name,
                "--description",
                desc,
                "--content-file",
                str(skill_md_path.resolve()),
            ]
        )
        if res.returncode != 0:
            err = res.stderr.strip()
            if "already exists" in err:
                refreshed = self.get_multica_skills()
                refreshed_id = refreshed.get(name)
                if refreshed_id:
                    print(f"  OK Skill '{name}' already exists ({refreshed_id})")
                    return refreshed_id
            print(f"  x Failed to create skill '{name}': {err}", file=sys.stderr)
            return None

        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError:
            print(f"  OK Created skill '{name}' (ID not found in output)")
            return None

        skill_id = data.get("id")
        if skill_id:
            print(f"  OK Created skill '{name}' ({skill_id})")
            return skill_id
        print(f"  OK Created skill '{name}' (ID not found in output)")
        return None

    def sync_baseline_skills(self, *, dry_run: bool = False) -> list[str]:
        local = self.get_local_skills()
        if not local:
            print("No local skills found in", self.skills_dir)
            return []

        baseline_names = [name for name in local if name in self.baseline_skills]
        print(f"Syncing {len(baseline_names)} baseline skill(s) from {self.skills_dir} to Multica workspace...")

        skill_ids: list[str] = []
        failed = 0
        for name in baseline_names:
            skill_id = self.create_or_update_skill(name, local[name], dry_run=dry_run)
            if skill_id:
                skill_ids.append(skill_id)
            elif not dry_run:
                failed += 1

        print(f"\nSkills: {len(skill_ids)}/{len(baseline_names)} synced" + (f", {failed} failed" if failed else ""))
        return skill_ids

    def resolve_skill_ids(self, skill_names: list[str]) -> tuple[list[str], list[str]]:
        existing = self.get_multica_skills()
        resolved: list[str] = []
        missing: list[str] = []
        for name in skill_names:
            skill_id = existing.get(name)
            if skill_id:
                resolved.append(skill_id)
            else:
                missing.append(name)
        return resolved, missing

    def get_all_agent_ids(self) -> list[tuple[str, str]]:
        res = self._run_cmd(["multica", "agent", "list"])
        if res.returncode != 0:
            print(f"  x Failed to list agents: {res.stderr.strip()}", file=sys.stderr)
            return []
        agents: list[tuple[str, str]] = []
        for line in res.stdout.strip().splitlines()[1:]:
            parts = line.split(maxsplit=3)
            if len(parts) >= 2:
                agents.append((parts[0], parts[1]))
        return agents

    def assign_skills_to_agent(
        self,
        agent_id: str,
        agent_name: str,
        skill_ids: list[str],
        *,
        dry_run: bool = False,
    ) -> bool:
        if not skill_ids:
            return True

        if dry_run:
            print(f"  [dry-run] multica agent skills set {agent_id} --skill-ids <{len(skill_ids)} skills>")
            return True

        res = self._run_cmd(
            [
                "multica",
                "agent",
                "skills",
                "set",
                agent_id,
                "--skill-ids",
                ",".join(skill_ids),
            ]
        )
        if res.returncode != 0:
            print(f"  x Failed to assign skills to '{agent_name}' ({agent_id[:8]}...): {res.stderr.strip()}", file=sys.stderr)
            return False
        print(f"  OK Assigned {len(skill_ids)} skills to '{agent_name}'")
        return True

    def assign_skills_to_all_agents(self, skill_ids: list[str], *, dry_run: bool = False) -> bool:
        agents = self.get_all_agent_ids()
        if not agents:
            print("No agents found in workspace")
            return False

        print(f"\nAssigning {len(skill_ids)} skill(s) to {len(agents)} agent(s)...")
        failed = 0
        for agent_id, agent_name in agents:
            if not self.assign_skills_to_agent(agent_id, agent_name, skill_ids, dry_run=dry_run):
                failed += 1

        success = len(agents) - failed
        print(f"\nAgents: {success}/{len(agents)} assigned" + (f", {failed} failed" if failed else ""))
        return failed == 0

    def _description_from_skill(self, skill_md_path: Path, fallback: str) -> str:
        if not skill_md_path.exists():
            return fallback
        first_line = skill_md_path.read_text(encoding="utf-8").splitlines()[0]
        return first_line.strip().lstrip("# ").strip()[:200] or fallback
```

- [ ] **Step 2: Replace bootstrap wrapper with service delegation**

Replace `src/bootstrap_multica_skills.py` with this complete content:

```python
#!/usr/bin/env python3
"""Bootstrap local skills into the Multica workspace."""

import argparse
from pathlib import Path

from src.core.services.multica_skill_service import (
    DEFAULT_BASELINE_SKILLS,
    DEFAULT_SKILLS_DIR,
    MulticaSkillService,
    run_multica_command,
)


SKILLS_DIR = DEFAULT_SKILLS_DIR
CORE_SKILLS = DEFAULT_BASELINE_SKILLS


def get_local_skills() -> dict[str, Path]:
    return MulticaSkillService().get_local_skills()


def get_multica_skills() -> dict[str, str]:
    return MulticaSkillService().get_multica_skills()


def create_or_update_skill(name: str, skill_md_path: Path, *, dry_run: bool = False) -> str | None:
    return MulticaSkillService().create_or_update_skill(name, skill_md_path, dry_run=dry_run)


def get_all_agent_ids() -> list[tuple[str, str]]:
    return MulticaSkillService().get_all_agent_ids()


def assign_skills_to_agent(agent_id: str, agent_name: str, skill_ids: list[str], *, dry_run: bool = False) -> bool:
    return MulticaSkillService().assign_skills_to_agent(agent_id, agent_name, skill_ids, dry_run=dry_run)


def sync_skills_to_multica(*, dry_run: bool = False) -> list[str]:
    return MulticaSkillService().sync_baseline_skills(dry_run=dry_run)


def assign_skills_to_all_agents(skill_ids: list[str], *, dry_run: bool = False) -> bool:
    return MulticaSkillService().assign_skills_to_all_agents(skill_ids, dry_run=dry_run)


def run(args) -> bool:
    dry_run = getattr(args, "dry_run", False)
    service = MulticaSkillService()
    skill_ids = service.sync_baseline_skills(dry_run=dry_run)
    if not skill_ids:
        if not dry_run:
            print("No skills to assign. Check that local skills exist and are importable.")
        return False
    return service.assign_skills_to_all_agents(skill_ids, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap skills from local filesystem to Multica workspace")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Print actions without executing")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run service tests**

Run:

```bash
python -m unittest tests.test_multica_skill_service
```

Expected: all tests pass.

- [ ] **Step 4: Run existing bootstrap and CLI tests for regressions**

Run:

```bash
python -m unittest tests.test_cli tests.test_bootstrap_gitnexus
```

Expected: all tests pass or fail only where later tasks intentionally change bootstrap order assertions.

- [ ] **Step 5: Commit service implementation**

Run:

```bash
git add src/core/services/multica_skill_service.py src/bootstrap_multica_skills.py tests/test_multica_skill_service.py
git commit -m "feat: add multica skill service"
```

---

### Task 3: Add Per-Agent Skill Binding To Multica Adapter

**Files:**
- Modify: `tests/test_multica_adapter.py`
- Modify: `src/adapters/multica_adapter.py`

- [ ] **Step 1: Add failing adapter tests**

Append these test methods before `test_publish_invalid_type` in `tests/test_multica_adapter.py`:

```python
    @patch("subprocess.run")
    def test_publish_agent_assigns_iac_declared_skills(self, mock_run):
        mock_get = MagicMock(returncode=0, stdout='{"id": "resolved-uuid", "instructions": ""}')
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = make_smart_mock([mock_get, mock_update])

        skill_service = MagicMock()
        skill_service.resolve_skill_ids.return_value = (["skill-1", "skill-2"], [])
        skill_service.assign_skills_to_agent.return_value = True

        adapter = MulticaAdapter(skill_service=skill_service)
        agent = Agent(
            id="coder",
            role="Coder",
            instructions="Code.",
            description="Coder",
            iac_schema={"agent": {"skills": ["brainstorming", "writing-plans"]}},
        )

        success = adapter.publish(agent)

        self.assertTrue(success)
        skill_service.resolve_skill_ids.assert_called_once_with(["brainstorming", "writing-plans"])
        skill_service.assign_skills_to_agent.assert_called_once_with(
            "resolved-uuid",
            "coder",
            ["skill-1", "skill-2"],
        )

    @patch("subprocess.run")
    def test_publish_agent_fails_when_iac_skill_missing(self, mock_run):
        mock_get = MagicMock(returncode=0, stdout='{"id": "resolved-uuid", "instructions": ""}')
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = make_smart_mock([mock_get, mock_update])

        skill_service = MagicMock()
        skill_service.resolve_skill_ids.return_value = (["skill-1"], ["missing-skill"])

        adapter = MulticaAdapter(skill_service=skill_service)
        agent = Agent(
            id="coder",
            role="Coder",
            instructions="Code.",
            iac_schema={"agent": {"skills": ["brainstorming", "missing-skill"]}},
        )

        success = adapter.publish(agent)

        self.assertFalse(success)
        skill_service.assign_skills_to_agent.assert_not_called()

    @patch("subprocess.run")
    def test_publish_agent_fails_when_iac_skill_assignment_fails(self, mock_run):
        mock_get = MagicMock(returncode=0, stdout='{"id": "resolved-uuid", "instructions": ""}')
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = make_smart_mock([mock_get, mock_update])

        skill_service = MagicMock()
        skill_service.resolve_skill_ids.return_value = (["skill-1"], [])
        skill_service.assign_skills_to_agent.return_value = False

        adapter = MulticaAdapter(skill_service=skill_service)
        agent = Agent(
            id="coder",
            role="Coder",
            instructions="Code.",
            iac_schema={"agent": {"skills": ["brainstorming"]}},
        )

        success = adapter.publish(agent)

        self.assertFalse(success)
        skill_service.assign_skills_to_agent.assert_called_once_with("resolved-uuid", "coder", ["skill-1"])

    @patch("subprocess.run")
    def test_publish_agent_without_iac_skills_does_not_assign_skills(self, mock_run):
        mock_get = MagicMock(returncode=0, stdout='{"id": "resolved-uuid", "instructions": ""}')
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = make_smart_mock([mock_get, mock_update])

        skill_service = MagicMock()
        adapter = MulticaAdapter(skill_service=skill_service)
        agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")

        success = adapter.publish(agent)

        self.assertTrue(success)
        skill_service.resolve_skill_ids.assert_not_called()
        skill_service.assign_skills_to_agent.assert_not_called()
```

- [ ] **Step 2: Run the adapter tests to verify they fail**

Run:

```bash
python -m unittest tests.test_multica_adapter
```

Expected: failures mention `MulticaAdapter.__init__()` does not accept `skill_service`.

- [ ] **Step 3: Update `MulticaAdapter` constructor and agent publish flow**

In `src/adapters/multica_adapter.py`, add this import near the other imports:

```python
from src.core.services.multica_skill_service import MulticaSkillService
```

Replace the constructor with:

```python
    def __init__(self, runtime_id: str = None, skill_service: MulticaSkillService = None):
        self.runtime_id = runtime_id
        self.skill_service = skill_service
```

Replace `_publish_agent` with this complete method:

```python
    def _publish_agent(self, agent: Agent) -> bool:
        print(f"Syncing agent {agent.id}...")

        found, actual_id, _ = self._resolve_agent_uuid(agent.id)

        if found:
            print(f"  Agent '{agent.id}' exists. Updating...")
            cmd = [
                "multica", "agent", "update", actual_id,
                "--instructions", agent.instructions
            ]
            if agent.description:
                cmd += ["--description", agent.description]
        else:
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

        res = self._run_cmd(cmd)
        if res.returncode != 0:
            err_msg = res.stderr.strip() if res.stderr else "Unknown error"
            print(f"  ✗ Failed to sync '{agent.id}': {err_msg}", file=sys.stderr)
            return False

        print(f"  ✓ Successfully synced '{agent.id}'")
        if not actual_id:
            actual_id = self._get_agent_uuid(agent.id)
        if not actual_id:
            print(f"  ✗ Failed to resolve UUID for agent '{agent.id}'", file=sys.stderr)
            return False

        return self._assign_agent_iac_skills(agent, actual_id)
```

Add this helper method directly after `_publish_agent`:

```python
    def _assign_agent_iac_skills(self, agent: Agent, agent_uuid: str) -> bool:
        skill_names = self._get_agent_iac_skill_names(agent)
        if not skill_names:
            return True

        service = self.skill_service or MulticaSkillService()
        skill_ids, missing = service.resolve_skill_ids(skill_names)
        if missing:
            print(
                f"  ✗ Agent '{agent.id}' declares missing Multica skill(s): {', '.join(missing)}",
                file=sys.stderr,
            )
            return False

        if not service.assign_skills_to_agent(agent_uuid, agent.id, skill_ids):
            return False
        return True

    def _get_agent_iac_skill_names(self, agent: Agent) -> list[str]:
        if not isinstance(agent.iac_schema, dict):
            return []
        agent_spec = agent.iac_schema.get("agent")
        if not isinstance(agent_spec, dict):
            return []
        skills = agent_spec.get("skills", [])
        if not isinstance(skills, list):
            return []
        return [skill for skill in skills if isinstance(skill, str) and skill]
```

- [ ] **Step 4: Run adapter tests**

Run:

```bash
python -m unittest tests.test_multica_adapter
```

Expected: all tests pass.

- [ ] **Step 5: Run service and agent repository tests**

Run:

```bash
python -m unittest tests.test_multica_skill_service tests.test_fs_agent_repository tests.test_agent_service
```

Expected: all tests pass.

- [ ] **Step 6: Commit adapter skill binding**

Run:

```bash
git add src/adapters/multica_adapter.py tests/test_multica_adapter.py
git commit -m "feat: bind iac skills when publishing multica agents"
```

---

### Task 4: Reorder Bootstrap And Wire CLI Tests

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/adapters/cli/entrypoint.py`

- [ ] **Step 1: Add failing CLI tests**

In `tests/test_cli.py`, update `test_bootstrap_cli_success` decorators and assertions to include baseline import before agent sync and baseline assignment after workflow sync:

```python
    @patch("src.adapters.cli.entrypoint.run_bootstrap_skills_assign_all")
    @patch("src.adapters.cli.entrypoint.run_sync_workflow")
    @patch("src.adapters.cli.entrypoint.run_sync_agent")
    @patch("src.adapters.cli.entrypoint.import_baseline_skills")
    @patch("src.adapters.cli.entrypoint.install_gitnexus")
    @patch("src.adapters.cli.entrypoint.install_skills_from_file")
    @patch("src.adapters.cli.entrypoint.run_bootstrap")
    def test_bootstrap_cli_success(
        self,
        mock_run_bootstrap,
        mock_install_skills,
        mock_install_gitnexus,
        mock_import_baseline_skills,
        mock_run_sync_agent,
        mock_run_sync_workflow,
        mock_assign_all,
    ):
        call_order = []
        mock_run_bootstrap.side_effect = lambda args: call_order.append("wiki")
        mock_install_skills.side_effect = lambda *args, **kwargs: call_order.append("install-skills")
        mock_install_gitnexus.side_effect = lambda *args, **kwargs: call_order.append("gitnexus")
        mock_import_baseline_skills.side_effect = lambda args: call_order.append("import-baseline") or ["skill-1"]
        mock_run_sync_agent.side_effect = lambda args: call_order.append("sync-agent")
        mock_run_sync_workflow.side_effect = lambda args: call_order.append("sync-workflow")
        mock_assign_all.side_effect = lambda args, skill_ids: call_order.append(f"assign-all:{','.join(skill_ids)}")

        test_args = [
            "cli.py",
            "bootstrap",
            "--repo",
            "org/private-kb",
            "--workflow",
            "workflow.yaml",
            "--dry-run",
        ]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        self.assertEqual(
            call_order,
            [
                "wiki",
                "install-skills",
                "gitnexus",
                "import-baseline",
                "sync-agent",
                "sync-workflow",
                "assign-all:skill-1",
            ],
        )
```

Add this new test after the GitNexus CLI tests:

```python
    @patch("src.adapters.cli.entrypoint.run_bootstrap_skills")
    def test_bootstrap_skills_cli_success(self, mock_run_bootstrap_skills):
        test_args = ["cli.py", "bootstrap-skills", "--dry-run"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        mock_run_bootstrap_skills.assert_called_once()
```

- [ ] **Step 2: Run CLI tests to verify failures**

Run:

```bash
python -m unittest tests.test_cli
```

Expected: failures mention missing `import_baseline_skills` or `run_bootstrap_skills_assign_all`.

- [ ] **Step 3: Update CLI bootstrap helpers and ordering**

In `src/adapters/cli/entrypoint.py`, add this import:

```python
from src.core.services.multica_skill_service import MulticaSkillService
```

Replace `run_bootstrap_skills` and `cmd_bootstrap` with these complete functions:

```python
def run_bootstrap_skills(args):
    skill_ids = import_baseline_skills(args)
    if not skill_ids:
        if not args.dry_run:
            print("No skills to assign. Check that local skills exist and are importable.")
            return False
        return True
    return run_bootstrap_skills_assign_all(args, skill_ids)


def import_baseline_skills(args):
    service = MulticaSkillService()
    return service.sync_baseline_skills(dry_run=args.dry_run)


def run_bootstrap_skills_assign_all(args, skill_ids: list[str]) -> bool:
    service = MulticaSkillService()
    return service.assign_skills_to_all_agents(skill_ids, dry_run=args.dry_run)


def cmd_bootstrap(args):
    try:
        run_bootstrap(args)
        install_skills_from_file(Path(args.skills_file), dry_run=args.dry_run)
        install_gitnexus(dry_run=args.dry_run)
        skill_ids = import_baseline_skills(args)
        if not skill_ids and not args.dry_run:
            raise RuntimeError("No baseline skills were imported into Multica")
        run_sync_agent(args)
        run_sync_workflow(args)
        if skill_ids and not run_bootstrap_skills_assign_all(args, skill_ids):
            raise RuntimeError("Failed to assign baseline skills to all agents")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python -m unittest tests.test_cli
```

Expected: all tests pass.

- [ ] **Step 5: Run service, adapter, and CLI tests together**

Run:

```bash
python -m unittest tests.test_multica_skill_service tests.test_multica_adapter tests.test_cli
```

Expected: all tests pass.

- [ ] **Step 6: Commit CLI ordering**

Run:

```bash
git add src/adapters/cli/entrypoint.py tests/test_cli.py
git commit -m "feat: reorder bootstrap skill import and assignment"
```

---

### Task 5: Add Makefile Target And Visibility Test

**Files:**
- Modify: `Makefile`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add failing Makefile visibility test**

Add this import near the top of `tests/test_cli.py`:

```python
import subprocess
```

Add this test method before the `if __name__ == "__main__":` block:

```python
    def test_make_help_shows_bootstrap_skills_target(self):
        result = subprocess.run(
            ["make", "help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("bootstrap-skills", result.stdout)
        self.assertIn("Import local skills into Multica", result.stdout)
```

- [ ] **Step 2: Run the visibility test to verify it fails**

Run:

```bash
python -m unittest tests.test_cli.TestCLI.test_make_help_shows_bootstrap_skills_target
```

Expected: failure because `bootstrap-skills` is not in `make help`.

- [ ] **Step 3: Add Makefile target**

In `Makefile`, update `.PHONY` from:

```make
.PHONY: create validate apply install-skills bootstrap bootstrap-wiki sync-agent sync-workflow test help
```

to:

```make
.PHONY: create validate apply install-skills bootstrap-skills bootstrap bootstrap-wiki sync-agent sync-workflow test help
```

Add this target after `install-skills`:

```make
bootstrap-skills: ## Import local skills into Multica and assign them to agents
	$(PYTHON) -m src.cli bootstrap-skills $(if $(DRY_RUN),--dry-run)
```

- [ ] **Step 4: Run Makefile visibility test**

Run:

```bash
python -m unittest tests.test_cli.TestCLI.test_make_help_shows_bootstrap_skills_target
```

Expected: pass.

- [ ] **Step 5: Run full CLI tests**

Run:

```bash
python -m unittest tests.test_cli
```

Expected: all tests pass.

- [ ] **Step 6: Commit Makefile target**

Run:

```bash
git add Makefile tests/test_cli.py
git commit -m "feat: expose bootstrap skills make target"
```

---

### Task 6: Verify Dry-Run CLI Behavior

**Files:**
- Modify: tests only if a dry-run assertion fails for a real defect found in this task.

- [ ] **Step 1: Run bootstrap-skills dry-run command**

Run:

```bash
python -m src.cli bootstrap-skills --dry-run
```

Expected: command exits `0`. It prints local skill import/assignment dry-run output or prints that no local skills were found. It does not execute mutating `multica` commands.

- [ ] **Step 2: Run umbrella bootstrap dry-run command**

Run:

```bash
python -m src.cli bootstrap --repo org/private-kb --workflow workflow/development.yaml --dry-run
```

Expected: command exits `0` if dry-run has enough local context. Output order shows wiki bootstrap, local skills install, GitNexus install, Multica baseline skill import, agent sync, workflow sync, and baseline assignment.

- [ ] **Step 3: If dry-run exits non-zero because of missing local context, add a focused test instead of weakening runtime behavior**

If Step 2 fails because the local machine lacks optional runtime context, add this test to `tests/test_cli.py`:

```python
    @patch("src.adapters.cli.entrypoint.run_bootstrap_skills_assign_all")
    @patch("src.adapters.cli.entrypoint.run_sync_workflow")
    @patch("src.adapters.cli.entrypoint.run_sync_agent")
    @patch("src.adapters.cli.entrypoint.import_baseline_skills")
    @patch("src.adapters.cli.entrypoint.install_gitnexus")
    @patch("src.adapters.cli.entrypoint.install_skills_from_file")
    @patch("src.adapters.cli.entrypoint.run_bootstrap")
    def test_bootstrap_dry_run_allows_no_imported_skill_ids(
        self,
        mock_run_bootstrap,
        mock_install_skills,
        mock_install_gitnexus,
        mock_import_baseline_skills,
        mock_run_sync_agent,
        mock_run_sync_workflow,
        mock_assign_all,
    ):
        mock_import_baseline_skills.return_value = []

        test_args = ["cli.py", "bootstrap", "--repo", "org/private-kb", "--workflow", "workflow.yaml", "--dry-run"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        mock_run_sync_agent.assert_called_once()
        mock_run_sync_workflow.assert_called_once()
        mock_assign_all.assert_not_called()
```

Run:

```bash
python -m unittest tests.test_cli.TestCLI.test_bootstrap_dry_run_allows_no_imported_skill_ids
```

Expected: pass.

- [ ] **Step 4: Commit any dry-run test adjustment**

If Step 3 changed tests, run:

```bash
git add tests/test_cli.py
git commit -m "test: cover bootstrap dry-run without imported skills"
```

If Step 3 was not needed, do not create a commit for this task.

---

### Task 7: Full Regression Verification

**Files:**
- No planned file changes.

- [ ] **Step 1: Run all unit tests**

Run:

```bash
python -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 2: Inspect worktree**

Run:

```bash
git status --short
```

Expected: only user-owned pre-existing changes remain outside committed task work. At the start of planning, those were `skills.txt` and `scratch/`; do not revert or commit them unless the user explicitly asks.

- [ ] **Step 3: Capture final implementation summary**

Record these facts for the final response:

```text
- Created MulticaSkillService for baseline skill import and assignment.
- Refactored bootstrap_multica_skills.py into a wrapper.
- Added per-agent IaC skill binding in MulticaAdapter.
- Reordered umbrella bootstrap so baseline skills are imported before agent sync and assigned after workflow sync.
- Added Makefile bootstrap-skills target.
- Verification command: python -m unittest discover -s tests
```


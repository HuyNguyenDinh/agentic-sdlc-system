"""Tests for bootstrap_multica_skills.py

TDD: written before implementation to drive the refactor that:
- Removes CORE_SKILLS constant
- Wires in SkillsCatalogService to filter which skills to sync
- Removes assign_skills_to_all_agents()
"""

import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path


class TestSyncSkillsFiltersByCatalog(unittest.TestCase):
    """test_sync_skills_filters_by_catalog: with a mock catalog returning
    {"shared": ["brainstorming", "writing-plans"]}, local skills dir has
    brainstorming/, writing-plans/, and irrelevant-skill/.
    Only brainstorming and writing-plans get synced."""

    def setUp(self):
        self.mock_catalog = MagicMock()
        self.mock_catalog.get_all_skills.return_value = {
            "shared": ["brainstorming", "writing-plans"]
        }

    def test_sync_skills_filters_by_catalog(self, tmp_path=None):
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            skills_dir = Path(td)
            # Create three skill directories
            for skill in ["brainstorming", "writing-plans", "irrelevant-skill"]:
                skill_dir = skills_dir / skill
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(f"# {skill}\nContent for {skill}.")

            with patch("src.bootstrap_multica_skills.SKILLS_DIR", skills_dir), \
                 patch("src.bootstrap_multica_skills.create_or_update_skill") as mock_create:
                mock_create.return_value = "skill-id-123"

                from src.bootstrap_multica_skills import sync_skills_to_multica
                result = sync_skills_to_multica(catalog=self.mock_catalog, dry_run=False)

        # Only brainstorming and writing-plans should have been processed
        synced_names = [c.args[0] for c in mock_create.call_args_list]
        self.assertIn("brainstorming", synced_names)
        self.assertIn("writing-plans", synced_names)
        self.assertNotIn("irrelevant-skill", synced_names)
        self.assertEqual(len(synced_names), 2)


class TestSyncSkillsNoFilterWithoutCatalog(unittest.TestCase):
    """test_sync_skills_no_filter_without_catalog: no catalog passed,
    ALL local skills get synced (no filter)."""

    def test_sync_skills_no_filter_without_catalog(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            skills_dir = Path(td)
            for skill in ["brainstorming", "writing-plans", "irrelevant-skill"]:
                skill_dir = skills_dir / skill
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(f"# {skill}\nContent.")

            with patch("src.bootstrap_multica_skills.SKILLS_DIR", skills_dir), \
                 patch("src.bootstrap_multica_skills.create_or_update_skill") as mock_create:
                mock_create.return_value = "skill-id-999"

                from src.bootstrap_multica_skills import sync_skills_to_multica
                result = sync_skills_to_multica(dry_run=False)  # no catalog

        synced_names = [c.args[0] for c in mock_create.call_args_list]
        self.assertIn("brainstorming", synced_names)
        self.assertIn("writing-plans", synced_names)
        self.assertIn("irrelevant-skill", synced_names)
        self.assertEqual(len(synced_names), 3)


class TestSyncSkillsDryRun(unittest.TestCase):
    """test_sync_skills_dry_run: dry run prints but doesn't call multica skill create."""

    def test_sync_skills_dry_run_does_not_call_multica(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            skills_dir = Path(td)
            skill_dir = skills_dir / "brainstorming"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# brainstorming\nContent.")

            mock_catalog = MagicMock()
            mock_catalog.get_all_skills.return_value = {"shared": ["brainstorming"]}

            with patch("src.bootstrap_multica_skills.SKILLS_DIR", skills_dir), \
                 patch("src.bootstrap_multica_skills._run_cmd") as mock_run_cmd:

                from src.bootstrap_multica_skills import sync_skills_to_multica
                result = sync_skills_to_multica(catalog=mock_catalog, dry_run=True)

        # dry-run returns an empty list (no real IDs created)
        self.assertEqual(result, [])

        # _run_cmd must NOT be called for actual skill creation
        for c in mock_run_cmd.call_args_list:
            cmd_args = c.args[0] if c.args else c.kwargs.get("args", [])
            self.assertFalse(
                cmd_args[:3] == ["multica", "skill", "create"],
                f"dry_run=True should not call 'multica skill create', but got: {cmd_args}"
            )


class TestRunDoesNotCallAssignToAllAgents(unittest.TestCase):
    """test_run_does_not_call_assign_to_all_agents: run() calls sync_skills_to_multica
    but NOT assign_skills_to_all_agents (which no longer exists)."""

    def test_assign_skills_to_all_agents_does_not_exist(self):
        """The function assign_skills_to_all_agents must be removed from the module."""
        import src.bootstrap_multica_skills as mod
        self.assertFalse(
            hasattr(mod, "assign_skills_to_all_agents"),
            "assign_skills_to_all_agents must be removed from bootstrap_multica_skills"
        )

    def test_run_calls_sync_skills_to_multica(self):
        """run() should call sync_skills_to_multica (with a catalog)."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            skills_dir = Path(td)

            with patch("src.bootstrap_multica_skills.SKILLS_DIR", skills_dir), \
                 patch("src.bootstrap_multica_skills.sync_skills_to_multica") as mock_sync, \
                 patch("src.bootstrap_multica_skills.SkillsCatalogService") as mock_svc_cls:
                mock_sync.return_value = []
                mock_catalog = MagicMock()
                mock_svc_cls.return_value = mock_catalog

                from src.bootstrap_multica_skills import run
                args = MagicMock()
                args.dry_run = False
                run(args)

        mock_sync.assert_called_once()
        # Verify catalog was passed
        call_kwargs = mock_sync.call_args.kwargs
        self.assertIn("catalog", call_kwargs)


if __name__ == "__main__":
    unittest.main()

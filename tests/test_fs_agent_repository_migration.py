import unittest
import tempfile
from pathlib import Path
from src.adapters.fs_agent_repository import FSAgentRepository


class TestFSAgentRepositoryMigration(unittest.TestCase):
    def test_legacy_agents_unchanged(self):
        """Verify 100% backward compatibility for legacy agents (no frontmatter)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Exact test file from original test - should behave identically
            agent_file = tmp_path / "pm-agent.md"
            agent_file.write_text(
                "### **Role**\n"
                "You are the PM Agent.\n"
                "### **Instructions**\n"
                "Follow the workflows strictly."
            )

            repo = FSAgentRepository(base_path=tmp_path)
            agents = repo.get_all_agents()

            self.assertEqual(len(agents), 1)
            self.assertEqual(agents[0].id, "pm-agent")
            self.assertEqual(agents[0].role, "You are the PM Agent.")
            self.assertIn("Follow the workflows strictly.", agents[0].instructions)
            self.assertIsNone(agents[0].iac_schema)

    def test_frontmatter_parsing_optional(self):
        """Agent with valid frontmatter loads correctly, legacy still works."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            agent_with_frontmatter = tmp_path / "engineer-agent.md"
            agent_with_frontmatter.write_text(
                "---\n"
                "iac:\n"
                "  name: engineer-agent\n"
                "  version: 1.0.0\n"
                "  environment:\n"
                "    name: production\n"
                "  permissions:\n"
                "    allowed_tools: ['git', 'bash']\n"
                "    read_access: ['src/*']\n"
                "    write_access: ['src/*']\n"
                "  entrypoint: main.py\n"
                "---\n"
                "### **Role**\n"
                "You are the Engineer Agent.\n"
                "Write clean code.\n"
            )

            repo = FSAgentRepository(base_path=tmp_path)
            agents = repo.get_all_agents()

            self.assertEqual(len(agents), 1)
            self.assertEqual(agents[0].role, "You are the Engineer Agent.")
            self.assertIn("Write clean code.", agents[0].instructions)
            self.assertIsNotNone(agents[0].iac_schema)
            self.assertEqual(agents[0].iac_schema['name'], 'engineer-agent')
            self.assertEqual(agents[0].iac_schema['version'], '1.0.0')

    def test_invalid_frontmatter_fallback(self):
        """Invalid frontmatter falls back to full content, no crash."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            agent_bad_frontmatter = tmp_path / "broken-agent.md"
            agent_bad_frontmatter.write_text(
                "---\n"
                "invalid: yaml\n"
                "this breaks [\n"
                "---\n"
                "### **Role**\n"
                "You are the Broken Agent.\n"
            )

            repo = FSAgentRepository(base_path=tmp_path)
            agents = repo.get_all_agents()

            self.assertEqual(len(agents), 1)
            self.assertEqual(agents[0].role, "You are the Broken Agent.")
            self.assertIsNone(agents[0].iac_schema)
            self.assertIn("invalid: yaml", agents[0].instructions)


if __name__ == "__main__":
    unittest.main()

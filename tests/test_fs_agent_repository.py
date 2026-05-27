import unittest
import tempfile
from pathlib import Path
from src.adapters.fs_agent_repository import FSAgentRepository

class TestFSAgentRepository(unittest.TestCase):
    def test_scan_and_parse_agents(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
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

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
from src.adapters.multica_adapter import MulticaAdapter
from src.core.domain.models import Agent

class TestMulticaAdapter(unittest.TestCase):
    @patch("subprocess.run")
    def test_publish_agent_create_flow(self, mock_run):
        # 1. Mock multica get command to return exit code 1 (agent does not exist)
        mock_get = MagicMock(returncode=1)
        # 2. Mock multica create command to return exit code 0 (success)
        mock_create = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_create]
        
        adapter = MulticaAdapter()
        agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")
        
        success = adapter.publish(agent)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "agent", "get", "coder"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Verify create command arguments
        mock_run.assert_any_call(
            ["multica", "agent", "create", "--name", "coder", "--instructions", "Code.", "--description", "Coder"],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("subprocess.run")
    def test_publish_agent_update_flow(self, mock_run):
        # 1. Mock multica get command to return exit code 0 (agent exists)
        mock_get = MagicMock(returncode=0)
        # 2. Mock multica update command to return exit code 0 (success)
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update]
        
        adapter = MulticaAdapter()
        agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")
        
        success = adapter.publish(agent)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify update command arguments
        mock_run.assert_any_call(
            ["multica", "agent", "update", "coder", "--instructions", "Code.", "--description", "Coder"],
            capture_output=True,
            text=True,
            check=False
        )

if __name__ == "__main__":
    unittest.main()

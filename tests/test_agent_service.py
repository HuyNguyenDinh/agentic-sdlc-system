import unittest
from unittest.mock import MagicMock
from src.core.services.agent_service import AgentService
from src.core.domain.models import Agent

class TestAgentService(unittest.TestCase):
    def test_sync_all_agents(self):
        mock_repo = MagicMock()
        mock_repo.get_all_agents.return_value = [
            Agent(id="pm", role="PM", instructions="Sync.")
        ]
        
        mock_pub = MagicMock()
        mock_pub.publish.return_value = True
        
        service = AgentService(agent_repo=mock_repo, agent_publisher=mock_pub)
        success, failed = service.sync_all_agents()
        
        self.assertEqual(success, 1)
        self.assertEqual(failed, 0)
        
        mock_repo.get_all_agents.assert_called_once()
        mock_pub.publish.assert_called_once_with(mock_repo.get_all_agents.return_value[0])

if __name__ == "__main__":
    unittest.main()

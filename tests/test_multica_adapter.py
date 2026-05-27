import unittest
from unittest.mock import patch, MagicMock
from src.adapters.multica_adapter import MulticaAdapter
from src.core.domain.models import Agent, Workflow

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

    @patch("subprocess.run")
    def test_publish_agent_create_flow_with_runtime_id(self, mock_run):
        # 1. Mock multica get command to return exit code 1 (agent does not exist)
        mock_get = MagicMock(returncode=1)
        # 2. Mock multica create command to return exit code 0 (success)
        mock_create = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_create]
        
        adapter = MulticaAdapter(runtime_id="my-test-runtime")
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
        
        # Verify create command arguments contains --runtime-id
        mock_run.assert_any_call(
            ["multica", "agent", "create", "--name", "coder", "--instructions", "Code.", "--runtime-id", "my-test-runtime", "--description", "Coder"],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_create_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 1 (squad does not exist)
        mock_get = MagicMock(returncode=1)
        # 2. Mock multica squad create command to return exit code 0 (success)
        mock_create = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_create]
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", description="Manage product features")
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "get", "product-squad"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Verify create command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "create", "--name", "product-squad", "--instructions", "# Product Squad\nDescription...", "--description", "Manage product features"],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_update_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 0 (squad exists)
        mock_get = MagicMock(returncode=0)
        # 2. Mock multica squad update command to return exit code 0 (success)
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update]
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", description="Manage product features")
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "get", "product-squad"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Verify update command arguments
        mock_run.assert_any_call(
            ["multica", "squad", "update", "product-squad", "--instructions", "# Product Squad\nDescription...", "--description", "Manage product features"],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_keyword_arguments(self, mock_run):
        mock_get = MagicMock(returncode=0)
        mock_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update]
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="kw-squad", instructions="instructions")
        
        # Test keyword calling convention
        success = adapter.publish(workflow=workflow)
        self.assertTrue(success)

    @patch("subprocess.run")
    def test_publish_workflow_failure_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 1 (squad does not exist)
        mock_get = MagicMock(returncode=1)
        # 2. Mock multica squad create command to return exit code 1 (failure)
        mock_create = MagicMock(returncode=1, stderr="Failed to create squad")
        mock_run.side_effect = [mock_get, mock_create]
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="product-squad", instructions="Description")
        
        success = adapter.publish(workflow)
        self.assertFalse(success)

    def test_publish_invalid_type(self):
        adapter = MulticaAdapter()
        with self.assertRaises(TypeError):
            adapter.publish("not a workflow or agent")

        with self.assertRaises(ValueError):
            adapter.publish(None)

if __name__ == "__main__":
    unittest.main()

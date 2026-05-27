import unittest
import json
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
        # 1. Mock multica get command to return exit code 0 (agent exists) with a JSON body
        mock_get = MagicMock(returncode=0, stdout='{"id": "resolved-uuid"}')
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
            ["multica", "agent", "update", "resolved-uuid", "--instructions", "Code.", "--description", "Coder"],
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
        # 3. Mock multica agent get command for squad leader
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "resolved-leader-uuid", "instructions": "base instruction"}')
        # 4. Mock multica agent update command
        mock_leader_update = MagicMock(returncode=0)
        # 5. Mock agent get + squad member add for each agent_id (2 agents → 4 calls)
        mock_agent1_get = MagicMock(returncode=0, stdout='{"id": "uuid-agent1", "instructions": ""}')
        mock_agent1_member = MagicMock(returncode=0)
        mock_agent2_get = MagicMock(returncode=0, stdout='{"id": "uuid-agent2", "instructions": ""}')
        mock_agent2_member = MagicMock(returncode=0)
        mock_run.side_effect = [
            mock_get, mock_create,
            mock_leader_get, mock_leader_update,
            mock_agent1_get, mock_agent1_member,
            mock_agent2_get, mock_agent2_member,
        ]
        
        adapter = MulticaAdapter()
        workflow = Workflow(
            id="product-squad",
            instructions="# Product Squad\nDescription...",
            squad_leader="product-lead-agent",
            description="Manage product features",
            agent_ids=["agent-one", "agent-two"],
        )
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 8)
        
        # Verify squad create
        mock_run.assert_any_call(
            ["multica", "squad", "create", "--name", "product-squad", "--leader", "product-lead-agent", "--description", "Manage product features"],
            capture_output=True, text=True, check=False
        )

        # Verify squad leader update
        expected_instructions = "base instruction\n\n<!-- WORKFLOW_START: product-squad -->\n# Product Squad\nDescription...\n<!-- WORKFLOW_END: product-squad -->"
        mock_run.assert_any_call(
            ["multica", "agent", "update", "resolved-leader-uuid", "--instructions", expected_instructions],
            capture_output=True, text=True, check=False
        )

        # Verify squad member add calls use the resolved UUIDs
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "product-squad", "--member-id", "uuid-agent1", "--type", "agent"],
            capture_output=True, text=True, check=False
        )
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "product-squad", "--member-id", "uuid-agent2", "--type", "agent"],
            capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_update_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 0 (squad exists)
        mock_get = MagicMock(returncode=0)
        # 2. Mock multica squad update command to return exit code 0 (success)
        mock_update = MagicMock(returncode=0)
        # 3. Mock multica agent get command for squad leader
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "resolved-leader-uuid", "instructions": "base instruction"}')
        # 4. Mock multica agent update command
        mock_leader_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update, mock_leader_get, mock_leader_update]
        
        adapter = MulticaAdapter()
        # No agent_ids → no member registration calls
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", squad_leader="product-lead-agent", description="Manage product features")
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 4)
        
        # Verify squad update uses --description (not --instructions)
        mock_run.assert_any_call(
            ["multica", "squad", "update", "product-squad", "--description", "Manage product features"],
            capture_output=True, text=True, check=False
        )

        expected_instructions = "base instruction\n\n<!-- WORKFLOW_START: product-squad -->\n# Product Squad\nDescription...\n<!-- WORKFLOW_END: product-squad -->"
        mock_run.assert_any_call(
            ["multica", "agent", "update", "resolved-leader-uuid", "--instructions", expected_instructions],
            capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_keyword_arguments(self, mock_run):
        mock_get = MagicMock(returncode=0)
        mock_update = MagicMock(returncode=0)
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "resolved-leader-uuid", "instructions": ""}')
        mock_leader_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update, mock_leader_get, mock_leader_update]
        
        adapter = MulticaAdapter()
        # No agent_ids — no extra member registration calls
        workflow = Workflow(id="kw-squad", instructions="instructions", squad_leader="leader-agent")
        
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
        workflow = Workflow(id="product-squad", instructions="Description", squad_leader="leader-agent")
        
        success = adapter.publish(workflow)
        self.assertFalse(success)

    @patch("subprocess.run")
    def test_publish_workflow_leader_update_failure(self, mock_run):
        # Squad creates successfully but leader update fails
        mock_get = MagicMock(returncode=1)
        mock_create = MagicMock(returncode=0)
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "resolved-leader-uuid", "instructions": ""}')
        mock_leader_update = MagicMock(returncode=1, stderr="Agent not found")
        mock_run.side_effect = [mock_get, mock_create, mock_leader_get, mock_leader_update]
        
        adapter = MulticaAdapter()
        # No agent_ids so no member registration runs after leader fails
        workflow = Workflow(id="product-squad", instructions="# Instructions", squad_leader="missing-agent", description="Desc")
        
        success = adapter.publish(workflow)
        self.assertFalse(success)

    @patch("subprocess.run")
    def test_publish_workflow_idempotent_flow(self, mock_run):
        # Verify that multiple runs replace the existing workflow instructions block instead of duplicating
        mock_get = MagicMock(returncode=0)
        mock_update = MagicMock(returncode=0)
        
        existing_instructions = (
            "base instruction\n\n"
            "<!-- WORKFLOW_START: product-squad -->\n"
            "# Product Squad\n"
            "OLD Description\n"
            "<!-- WORKFLOW_END: product-squad -->"
        )
        mock_leader_get = MagicMock(returncode=0, stdout=f'{{"id": "resolved-leader-uuid", "instructions": {json.dumps(existing_instructions)}}}')
        mock_leader_update = MagicMock(returncode=0)
        mock_run.side_effect = [mock_get, mock_update, mock_leader_get, mock_leader_update]
        
        adapter = MulticaAdapter()
        # No agent_ids so no member registration calls
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", squad_leader="product-lead-agent", description="Manage product features")
        
        success = adapter.publish(workflow)
        self.assertTrue(success)
        
        # Verify instructions were replaced, not duplicated
        expected_instructions = (
            "base instruction\n\n"
            "<!-- WORKFLOW_START: product-squad -->\n"
            "# Product Squad\n"
            "Description...\n"
            "<!-- WORKFLOW_END: product-squad -->"
        )
        mock_run.assert_any_call(
            ["multica", "agent", "update", "resolved-leader-uuid", "--instructions", expected_instructions],
            capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_squad_members(self, mock_run):
        """Verify that each agent_id is resolved and added as a squad member."""
        mock_squad_get = MagicMock(returncode=0)
        mock_squad_update = MagicMock(returncode=0)
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "uuid-leader", "instructions": ""}')
        mock_leader_update = MagicMock(returncode=0)
        # Three agents to register: each needs an agent get + squad member add
        mock_a_get = MagicMock(returncode=0, stdout='{"id": "uuid-a", "instructions": ""}')
        mock_a_add = MagicMock(returncode=0)
        mock_b_get = MagicMock(returncode=0, stdout='{"id": "uuid-b", "instructions": ""}')
        mock_b_add = MagicMock(returncode=0)
        # Agent C not found in Multica (returncode=1) → skipped
        mock_c_get = MagicMock(returncode=1)

        mock_run.side_effect = [
            mock_squad_get, mock_squad_update,
            mock_leader_get, mock_leader_update,
            mock_a_get, mock_a_add,
            mock_b_get, mock_b_add,
            mock_c_get,  # no member add — skipped
        ]

        adapter = MulticaAdapter()
        workflow = Workflow(
            id="my-squad",
            instructions="# My Squad",
            squad_leader="lead-agent",
            agent_ids=["agent-a", "agent-b", "agent-c"],
        )

        success = adapter.publish(workflow)
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 9)

        # agent-a and agent-b should have been added by UUID
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "my-squad", "--member-id", "uuid-a", "--type", "agent"],
            capture_output=True, text=True, check=False
        )
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "my-squad", "--member-id", "uuid-b", "--type", "agent"],
            capture_output=True, text=True, check=False
        )
        # agent-c was not found, so no member add call for it
        calls = [str(c) for c in mock_run.call_args_list]
        self.assertFalse(any("uuid-c" in c for c in calls))

    def test_publish_invalid_type(self):
        adapter = MulticaAdapter()
        with self.assertRaises(TypeError):
            adapter.publish("not a workflow or agent")

        with self.assertRaises(ValueError):
            adapter.publish(None)

if __name__ == "__main__":
    unittest.main()

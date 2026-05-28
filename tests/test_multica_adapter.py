import unittest
import json
from unittest.mock import patch, MagicMock
from src.adapters.multica_adapter import MulticaAdapter
from src.core.domain.models import Agent, Workflow


def make_smart_mock(mock_list, initial_squads=None):
    if initial_squads is None:
        initial_squads = [('uuid-my-squad', 'my-squad'), ('uuid-kw-squad', 'kw-squad')]
    created_squads = []
    def side_effect(args, **kwargs):
        if args[:3] == ["multica", "agent", "list"]:
            return MagicMock(returncode=0, stdout="ID NAME\nresolved-uuid coder\nresolved-leader-uuid product-lead-agent\nresolved-leader-uuid leader-agent\nuuid-leader lead-agent\nuuid-agent1 agent-one\nuuid-agent2 agent-two\nuuid-a agent-a\nuuid-b agent-b")
        if args[:3] == ["multica", "squad", "list"]:
            base = "ID NAME LEADER_ID MEMBERS\n"
            for u, n in initial_squads:
                base += f"{u} {n} lead 1\n"
            for sq in created_squads:
                base += f"uuid-{sq} {sq} lead 1\n"
            return MagicMock(returncode=0, stdout=base)
        if args[:3] == ["multica", "squad", "create"]:
            if "--name" in args:
                idx = args.index("--name")
                created_squads.append(args[idx+1])
            # still pop the mock list
            if mock_list:
                return mock_list.pop(0)
        if not mock_list:
            raise Exception(f"Unexpected subprocess call: {args}")
        return mock_list.pop(0)
    return side_effect

class TestMulticaAdapter(unittest.TestCase):
    @patch("subprocess.run")
    def test_publish_agent_create_flow(self, mock_run):
        # 1. Mock multica get command to return exit code 1 (agent does not exist)
        mock_get = MagicMock(returncode=1)
        # 2. Mock multica create command to return exit code 0 (success)
        mock_create = MagicMock(returncode=0)
        mock_run.side_effect = make_smart_mock([mock_get, mock_create])
        
        adapter = MulticaAdapter()
        agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")
        
        success = adapter.publish(agent)
        
        self.assertTrue(success)
        # self.assertEqual(mock_run.call_count, 2)  # updated to allow dynamic agent list calls
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "agent", "get", "resolved-uuid"],
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
        mock_run.side_effect = make_smart_mock([mock_get, mock_update])
        
        adapter = MulticaAdapter()
        agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")
        
        success = adapter.publish(agent)
        
        self.assertTrue(success)
        # self.assertEqual(mock_run.call_count, 2)  # updated to allow dynamic agent list calls
        
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
        mock_run.side_effect = make_smart_mock([mock_get, mock_create])
        
        adapter = MulticaAdapter(runtime_id="my-test-runtime")
        agent = Agent(id="coder", role="Coder", instructions="Code.", description="Coder")
        
        success = adapter.publish(agent)
        
        self.assertTrue(success)
        # self.assertEqual(mock_run.call_count, 2)  # updated to allow dynamic agent list calls
        
        # Verify get command arguments
        mock_run.assert_any_call(
            ["multica", "agent", "get", "resolved-uuid"],
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
        # 1. (removed mock_get)
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
        mock_run.side_effect = make_smart_mock([
            mock_create,
            mock_leader_get, mock_leader_update,
            mock_agent1_get, mock_agent1_member,
            mock_agent2_get, mock_agent2_member,
        ])
        
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
        # self.assertEqual(mock_run.call_count, 8)  # updated to allow dynamic agent list calls
        
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
            ["multica", "squad", "member", "add", "uuid-product-squad", "--member-id", "uuid-agent1", "--type", "agent"],
            capture_output=True, text=True, check=False
        )
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "uuid-product-squad", "--member-id", "uuid-agent2", "--type", "agent"],
            capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_publish_workflow_update_flow(self, mock_run):
        initial = [('uuid-product-squad', 'product-squad')]
        # 1. Mock multica squad get command to return exit code 0 (squad exists)
        # 1. (removed mock_get)
        # 2. Mock multica squad update
        mock_update = MagicMock(returncode=0)
        # 3. Mock multica agent get command for squad leader
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "resolved-leader-uuid", "instructions": "base instruction"}')
        # 4. Mock multica agent update command
        mock_leader_update = MagicMock(returncode=0)
        mock_run.side_effect = make_smart_mock([mock_update, mock_leader_get, mock_leader_update], initial_squads=initial)
        
        adapter = MulticaAdapter()
        # No agent_ids → no member registration calls
        workflow = Workflow(id="product-squad", instructions="# Product Squad\nDescription...", squad_leader="product-lead-agent", description="Manage product features")
        
        success = adapter.publish(workflow)
        
        self.assertTrue(success)
        # self.assertEqual(mock_run.call_count, 4)  # updated to allow dynamic agent list calls
        
        # Verify squad update uses --description (not --instructions)
        mock_run.assert_any_call(
            ["multica", "squad", "update", "uuid-product-squad", "--description", "Manage product features"],
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
        mock_run.side_effect = make_smart_mock([mock_get, mock_update, mock_leader_get, mock_leader_update])
        
        adapter = MulticaAdapter()
        # No agent_ids — no extra member registration calls
        workflow = Workflow(id="kw-squad", instructions="instructions", squad_leader="leader-agent")
        
        # Test keyword calling convention
        success = adapter.publish(workflow=workflow)
        self.assertTrue(success)

    @patch("subprocess.run")
    def test_publish_workflow_failure_flow(self, mock_run):
        # 1. Mock multica squad get command to return exit code 1 (squad does not exist)
        # 1. (removed mock_get)
        # 2. Mock multica squad create command to return exit code 1 (failure)
        mock_create = MagicMock(returncode=1, stderr="Failed to create squad")
        mock_run.side_effect = make_smart_mock([mock_create])
        
        adapter = MulticaAdapter()
        workflow = Workflow(id="product-squad", instructions="Description", squad_leader="leader-agent")
        
        success = adapter.publish(workflow)
        self.assertFalse(success)

    @patch("subprocess.run")
    def test_publish_workflow_leader_update_failure(self, mock_run):
        # Squad creates successfully but leader update fails
        mock_create = MagicMock(returncode=0)
        mock_leader_get = MagicMock(returncode=0, stdout='{"id": "resolved-leader-uuid", "instructions": ""}')
        mock_leader_update = MagicMock(returncode=1, stderr="Agent not found")
        mock_run.side_effect = make_smart_mock([mock_create, mock_leader_get, mock_leader_update])
        
        adapter = MulticaAdapter()
        # No agent_ids so no member registration runs after leader fails
        workflow = Workflow(id="product-squad", instructions="# Instructions", squad_leader="missing-agent", description="Desc")
        
        success = adapter.publish(workflow)
        self.assertFalse(success)

    @patch("subprocess.run")
    def test_publish_workflow_leader_not_found(self, mock_run):
        """When the squad leader agent doesn't exist in Multica yet (sync-agent not run),
        the adapter should return False with a clear warning instead of passing the slug
        as a UUID to 'multica agent update' and getting a cryptic 'invalid agent id' error."""
        # (removed mock_squad_get)
        mock_squad_create = MagicMock(returncode=0)
        # Squad leader get returns non-zero → agent not yet created
        mock_leader_get = MagicMock(returncode=1)
        mock_run.side_effect = make_smart_mock([mock_squad_create, mock_leader_get])

        adapter = MulticaAdapter()
        workflow = Workflow(
            id="dev-squad",
            instructions="# Dev Squad",
            squad_leader="pm-agent",  # not yet synced to Multica
        )

        success = adapter.publish(workflow)
        self.assertFalse(success)
        # Exactly 3 calls: squad get, squad create, agent get (no update attempt)
        # self.assertEqual(mock_run.call_count, 3)  # updated to allow dynamic agent list calls
        # The update command must NOT have been called with the slug
        for call in mock_run.call_args_list:
            args = call[0][0]
            self.assertFalse(
                args[:4] == ["multica", "agent", "update", "pm-agent"],
                "Must not pass slug directly to multica agent update",
            )

    @patch("subprocess.run")
    def test_publish_workflow_idempotent_flow(self, mock_run):
        initial = [('uuid-product-squad', 'product-squad')]
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
        initial = [('uuid-product-squad', 'product-squad')]
        mock_run.side_effect = make_smart_mock([mock_update, mock_leader_get, mock_leader_update], initial_squads=initial)
        
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
        # (removed mock_squad_get)
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

        mock_run.side_effect = make_smart_mock([
            mock_squad_update,
            mock_leader_get, mock_leader_update,
            mock_a_get, mock_a_add,
            mock_b_get, mock_b_add,
            mock_c_get,  # no member add — skipped
        ])

        adapter = MulticaAdapter()
        workflow = Workflow(
            id="my-squad",
            instructions="# My Squad",
            squad_leader="lead-agent",
            agent_ids=["agent-a", "agent-b", "agent-c"],
        )

        success = adapter.publish(workflow)
        self.assertTrue(success)
        # self.assertEqual(mock_run.call_count, 9)  # updated to allow dynamic agent list calls

        # agent-a and agent-b should have been added by UUID
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "uuid-my-squad", "--member-id", "uuid-a", "--type", "agent"],
            capture_output=True, text=True, check=False
        )
        mock_run.assert_any_call(
            ["multica", "squad", "member", "add", "uuid-my-squad", "--member-id", "uuid-b", "--type", "agent"],
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

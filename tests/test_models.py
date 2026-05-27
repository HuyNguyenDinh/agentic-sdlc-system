import unittest
from src.core.domain.models import Agent, Workflow

class TestDomainModels(unittest.TestCase):
    def test_agent_creation(self):
        agent = Agent(
            id="pm-agent",
            role="Squad Leader & Orchestrator",
            instructions="Orchestrate everything.",
            description="Project manager agent"
        )
        self.assertEqual(agent.id, "pm-agent")
        self.assertEqual(agent.role, "Squad Leader & Orchestrator")
        self.assertEqual(agent.instructions, "Orchestrate everything.")
        self.assertEqual(agent.description, "Project manager agent")

    def test_workflow_creation(self):
        workflow = Workflow(
            id="product-squad",
            instructions="# Product Squad\nDescription...",
            squad_leader="product-lead-agent",
            description="Manage product features"
        )
        self.assertEqual(workflow.id, "product-squad")
        self.assertEqual(workflow.instructions, "# Product Squad\nDescription...")
        self.assertEqual(workflow.squad_leader, "product-lead-agent")
        self.assertEqual(workflow.description, "Manage product features")

if __name__ == "__main__":
    unittest.main()

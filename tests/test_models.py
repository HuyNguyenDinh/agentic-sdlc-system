import unittest
from src.core.domain.models import Agent

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

if __name__ == "__main__":
    unittest.main()

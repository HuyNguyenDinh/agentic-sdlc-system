from src.core.ports.agent_repository import AgentRepositoryPort
from src.core.ports.agent_publisher import AgentPublisherPort

class AgentService:
    def __init__(self, agent_repo: AgentRepositoryPort, agent_publisher: AgentPublisherPort):
        self.agent_repo = agent_repo
        self.agent_publisher = agent_publisher

    def sync_all_agents(self) -> tuple[int, int]:
        agents = self.agent_repo.get_all_agents()
        print(f"Found {len(agents)} agents locally. Starting synchronization...")
        
        success_count = 0
        fail_count = 0
        
        for agent in agents:
            if self.agent_publisher.publish(agent):
                success_count += 1
            else:
                fail_count += 1
                
        print(f"\nDone. Synced: {success_count}, Failed: {fail_count}")
        return success_count, fail_count

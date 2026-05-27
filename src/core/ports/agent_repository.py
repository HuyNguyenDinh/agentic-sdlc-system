from abc import ABC, abstractmethod
from src.core.domain.models import Agent

class AgentRepositoryPort(ABC):
    @abstractmethod
    def get_all_agents(self) -> list[Agent]:
        """Recursively loads all agents from the storage/source."""
        pass

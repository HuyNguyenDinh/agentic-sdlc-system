from abc import ABC, abstractmethod
from src.core.domain.models import Agent

class AgentPublisherPort(ABC):
    @abstractmethod
    def publish(self, agent: Agent) -> bool:
        """Registers or updates the agent in the external system. Returns True on success."""
        pass

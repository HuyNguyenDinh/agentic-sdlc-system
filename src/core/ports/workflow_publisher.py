from abc import ABC, abstractmethod
from src.core.domain.models import Workflow

class WorkflowPublisherPort(ABC):
    @abstractmethod
    def publish(self, workflow: Workflow) -> bool:
        """Publishes a workflow to the external system. Returns True on success."""
        pass

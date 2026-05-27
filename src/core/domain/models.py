from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Agent:
    id: str
    role: str
    instructions: str
    description: Optional[str] = None


@dataclass(frozen=True)
class Workflow:
    """Represents an executable orchestration workflow containing agent/squad instructions."""
    id: str
    instructions: str
    squad_leader: str
    description: Optional[str] = None

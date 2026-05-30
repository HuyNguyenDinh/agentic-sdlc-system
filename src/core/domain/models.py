from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass(frozen=True)
class Agent:
    id: str
    role: str
    instructions: str
    description: Optional[str] = None
    iac_schema: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class Workflow:
    """Represents an executable orchestration workflow containing agent/squad instructions."""
    id: str
    instructions: str
    squad_leader: str
    description: Optional[str] = None
    agent_ids: List[str] = field(default_factory=list)

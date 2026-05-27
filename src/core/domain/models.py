from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Agent:
    id: str
    role: str
    instructions: str
    description: Optional[str] = None

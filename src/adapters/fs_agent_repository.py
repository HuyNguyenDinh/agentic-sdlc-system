import re
from pathlib import Path
from src.core.domain.models import Agent
from src.core.ports.agent_repository import AgentRepositoryPort

class FSAgentRepository(AgentRepositoryPort):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)

    def get_all_agents(self) -> list[Agent]:
        agents = []
        if not self.base_path.exists():
            return agents
            
        for p in self.base_path.rglob("*.md"):
            if p.name.startswith("."):
                continue
            content = p.read_text(encoding="utf-8")
            
            # Extract Role/Description
            role = None
            
            # Pattern 1: Inline Bold Role e.g., **Role:** Squad Leader & Orchestrator
            role_match = re.search(r"\*\*Role:\*\*?\s*(.*?)(?:\n|$)", content, re.IGNORECASE)
            if role_match:
                role = role_match.group(1).strip()
            
            # Pattern 2: Section Header Role e.g., ### **Role**\nYou are...
            if not role:
                role_match = re.search(r"###?\s+\*\*Role\*\*?\s*\n+(.*?)(?:\n|$)", content, re.IGNORECASE)
                if role_match:
                    role = role_match.group(1).strip()
            
            # Pattern 3: H1 Header e.g., # Product Lead Agent
            if not role:
                title_match = re.search(r"^#\s+(.*?)(?:\n|$)", content)
                if title_match:
                    role = title_match.group(1).strip()
            
            # Fallback to file stem prettified
            if not role:
                role = p.stem.replace("-", " ").title()

            agents.append(
                Agent(
                    id=p.stem,
                    role=role,
                    instructions=content,
                    description=role
                )
            )
        return sorted(agents, key=lambda a: a.id)

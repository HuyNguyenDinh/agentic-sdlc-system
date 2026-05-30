import re
import yaml
from pathlib import Path
from src.core.domain.models import Agent
from src.core.ports.agent_repository import AgentRepositoryPort
from src.core.schema.agent_iac_schema import validate_agent_iac

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
            raw_content = p.read_text(encoding="utf-8")

            # Split frontmatter and content
            frontmatter = None
            content = raw_content
            iac_schema = None

            if raw_content.startswith("---\n"):
                parts = raw_content.split("\n---\n", 2)
                if len(parts) >= 2:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        content = parts[2].lstrip("\n")

                        # Validate and load IaC schema if present
                        if isinstance(frontmatter, dict) and "iac" in frontmatter:
                            iac_schema = validate_agent_iac(frontmatter["iac"])
                    except Exception:
                        # Silently ignore invalid frontmatter - fall back to full content
                        content = raw_content
                        frontmatter = None
                        iac_schema = None

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
                    description=role,
                    iac_schema=iac_schema
                )
            )
        return sorted(agents, key=lambda a: a.id)

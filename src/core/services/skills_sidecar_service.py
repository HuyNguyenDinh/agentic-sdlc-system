from pathlib import Path
from typing import List
import yaml

from src.core.services.skills_catalog_service import SkillsCatalogService


class SkillsSidecarService:
    def __init__(self, catalog: SkillsCatalogService, agents_root: Path):
        self._catalog = catalog
        self._agents_root = agents_root

    def _find_sidecar(self, agent_id: str) -> Path | None:
        for path in self._agents_root.rglob(f"{agent_id}.skills.yaml"):
            return path
        return None

    def has_sidecar(self, agent_id: str) -> bool:
        return self._find_sidecar(agent_id) is not None

    def get_skills_for_agent(self, agent_id: str) -> List[str]:
        sidecar_path = self._find_sidecar(agent_id)
        if not sidecar_path:
            raise FileNotFoundError(f"No sidecar found for agent: {agent_id}")

        data = yaml.safe_load(sidecar_path.read_text())
        pull_paths: List[str] = data.get("pull", [])
        override = data.get("override", {})
        includes: List[str] = override.get("include", [])
        excludes: List[str] = override.get("exclude", [])

        skills: List[str] = []
        for pull_path in pull_paths:
            component = pull_path.rstrip("/").split("/")[-1]
            skills.extend(self._catalog.get_component_skills(component))

        skills = [s for s in skills if s not in excludes]
        for s in includes:
            if s not in skills:
                skills.append(s)

        return skills

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
import yaml

_HERE = Path(__file__).resolve()


@dataclass
class _RepoEntry:
    name: str
    install: str
    skills: List[str] = field(default_factory=list)


@dataclass
class _ComponentCatalog:
    component: str
    repos: List[_RepoEntry] = field(default_factory=list)


class SkillsCatalogService:
    def __init__(self, root: Path = None, project_root: Path = None):
        self._project_root = project_root or _HERE.parents[3]
        self._root = root or (self._project_root / "skills" / "skills.yaml")
        self._catalogs: List[_ComponentCatalog] = []
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        data = yaml.safe_load(self._root.read_text())
        for import_path in data.get("imports", []):
            component_file = self._project_root / import_path / "skills.yaml"
            comp_data = yaml.safe_load(component_file.read_text())
            repos = [
                _RepoEntry(name=r["name"], install=r["install"], skills=r.get("skills", []))
                for r in comp_data.get("repos", [])
            ]
            self._catalogs.append(_ComponentCatalog(component=comp_data["component"], repos=repos))
        self._loaded = True

    def get_install_urls(self) -> List[str]:
        self._load()
        seen: set = set()
        urls: List[str] = []
        for cat in self._catalogs:
            for repo in cat.repos:
                if repo.install not in seen:
                    seen.add(repo.install)
                    urls.append(repo.install)
        return urls

    def get_component_skills(self, component: str) -> List[str]:
        self._load()
        known = {cat.component for cat in self._catalogs}
        if component not in known:
            raise ValueError(f"Unknown component: {component}")
        for cat in self._catalogs:
            if cat.component == component:
                return [s for repo in cat.repos for s in repo.skills]
        return []

    def get_all_skills(self) -> Dict[str, List[str]]:
        self._load()
        return {
            cat.component: [s for repo in cat.repos for s in repo.skills]
            for cat in self._catalogs
        }

import pytest
import yaml
from src.core.services.skills_catalog_service import SkillsCatalogService
from src.core.services.skills_sidecar_service import SkillsSidecarService

CATALOG_ROOT = {"version": 1, "imports": ["skills/components/coding", "skills/components/shared"]}
CODING_COMPONENT = {
    "version": 1, "component": "coding",
    "repos": [{"name": "superpowers", "install": "https://github.com/obra/superpowers",
               "skills": ["test-driven-development", "systematic-debugging", "executing-plans"]}],
}
SHARED_COMPONENT = {
    "version": 1, "component": "shared",
    "repos": [{"name": "multica", "install": "https://github.com/org/multica",
               "skills": ["multica-collaboration"]}],
}


@pytest.fixture
def tmp_project(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "skills.yaml").write_text(yaml.dump(CATALOG_ROOT))
    coding_dir = skills_dir / "components" / "coding"
    coding_dir.mkdir(parents=True)
    (coding_dir / "skills.yaml").write_text(yaml.dump(CODING_COMPONENT))
    shared_dir = skills_dir / "components" / "shared"
    shared_dir.mkdir(parents=True)
    (shared_dir / "skills.yaml").write_text(yaml.dump(SHARED_COMPONENT))
    (tmp_path / "agents" / "coding").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sidecar_service(tmp_project):
    catalog = SkillsCatalogService(
        root=tmp_project / "skills" / "skills.yaml",
        project_root=tmp_project,
    )
    return SkillsSidecarService(catalog=catalog, agents_root=tmp_project / "agents")


def _write_sidecar(tmp_project, agent_id, data):
    path = tmp_project / "agents" / "coding" / f"{agent_id}.skills.yaml"
    path.write_text(yaml.dump(data))


def test_has_sidecar_true_when_file_exists(sidecar_service, tmp_project):
    _write_sidecar(tmp_project, "coder-agent", {"version": 1, "agent": "coder-agent", "pull": []})
    assert sidecar_service.has_sidecar("coder-agent") is True


def test_has_sidecar_false_when_missing(sidecar_service):
    assert sidecar_service.has_sidecar("ghost-agent") is False


def test_get_skills_resolves_pull(sidecar_service, tmp_project):
    _write_sidecar(tmp_project, "coder-agent", {
        "version": 1, "agent": "coder-agent",
        "pull": ["skills/components/coding"],
    })
    skills = sidecar_service.get_skills_for_agent("coder-agent")
    assert "test-driven-development" in skills
    assert "systematic-debugging" in skills


def test_get_skills_applies_exclude(sidecar_service, tmp_project):
    _write_sidecar(tmp_project, "coder-agent", {
        "version": 1, "agent": "coder-agent",
        "pull": ["skills/components/coding"],
        "override": {"exclude": ["systematic-debugging"]},
    })
    skills = sidecar_service.get_skills_for_agent("coder-agent")
    assert "systematic-debugging" not in skills
    assert "test-driven-development" in skills


def test_get_skills_applies_include(sidecar_service, tmp_project):
    _write_sidecar(tmp_project, "coder-agent", {
        "version": 1, "agent": "coder-agent",
        "pull": ["skills/components/coding"],
        "override": {"include": ["multica-collaboration"]},
    })
    skills = sidecar_service.get_skills_for_agent("coder-agent")
    assert "multica-collaboration" in skills
    assert "test-driven-development" in skills


def test_get_skills_raises_for_unknown_component(sidecar_service, tmp_project):
    _write_sidecar(tmp_project, "coder-agent", {
        "version": 1, "agent": "coder-agent",
        "pull": ["skills/components/unknown-component"],
    })
    with pytest.raises(ValueError, match="Unknown component: unknown-component"):
        sidecar_service.get_skills_for_agent("coder-agent")


def test_get_skills_raises_when_no_sidecar(sidecar_service):
    with pytest.raises(FileNotFoundError, match="No sidecar found for agent: ghost-agent"):
        sidecar_service.get_skills_for_agent("ghost-agent")

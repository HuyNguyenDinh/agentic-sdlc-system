import pytest
import yaml
from src.core.services.skills_catalog_service import SkillsCatalogService

FAKE_ROOT = {
    "version": 1,
    "imports": ["skills/components/coding", "skills/components/shared"],
}
FAKE_CODING = {
    "version": 1, "component": "coding",
    "repos": [{"name": "superpowers", "install": "https://github.com/obra/superpowers",
               "skills": ["test-driven-development", "systematic-debugging"]}],
}
FAKE_SHARED = {
    "version": 1, "component": "shared",
    "repos": [
        {"name": "multica", "install": "https://github.com/HuyNguyenDinh/multica-collaboration-skill",
         "skills": ["multica-collaboration"]},
        {"name": "superpowers", "install": "https://github.com/obra/superpowers",
         "skills": ["using-superpowers"]},
    ],
}


@pytest.fixture
def catalog(tmp_path):
    root = tmp_path / "skills" / "skills.yaml"
    root.parent.mkdir(parents=True)
    root.write_text(yaml.dump(FAKE_ROOT))
    coding_dir = tmp_path / "skills" / "components" / "coding"
    coding_dir.mkdir(parents=True)
    (coding_dir / "skills.yaml").write_text(yaml.dump(FAKE_CODING))
    shared_dir = tmp_path / "skills" / "components" / "shared"
    shared_dir.mkdir(parents=True)
    (shared_dir / "skills.yaml").write_text(yaml.dump(FAKE_SHARED))
    return SkillsCatalogService(root=root, project_root=tmp_path)


def test_get_install_urls_deduplicates_repos(catalog):
    urls = catalog.get_install_urls()
    assert urls.count("https://github.com/obra/superpowers") == 1


def test_get_install_urls_returns_all_unique_installs(catalog):
    urls = catalog.get_install_urls()
    assert len(urls) == 2
    assert "https://github.com/HuyNguyenDinh/multica-collaboration-skill" in urls


def test_get_component_skills_returns_skills_for_known_component(catalog):
    assert catalog.get_component_skills("coding") == ["test-driven-development", "systematic-debugging"]


def test_get_component_skills_raises_for_unknown_component(catalog):
    with pytest.raises(ValueError, match="Unknown component: unknown"):
        catalog.get_component_skills("unknown")


def test_get_all_skills_returns_map(catalog):
    all_skills = catalog.get_all_skills()
    assert "test-driven-development" in all_skills["coding"]
    assert "multica-collaboration" in all_skills["shared"]

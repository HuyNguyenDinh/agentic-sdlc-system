# Skills Module & Sidecar Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace global skill assignment with a centralized YAML catalog and per-agent sidecar files that explicitly pull skills by component.

**Architecture:** A root `skills/skills.yaml` imports component registries under `skills/components/`. Each agent gets a `{agent-id}.skills.yaml` sidecar that pulls from component paths. `SkillsCatalogService` reads the catalog; `SkillsSidecarService` resolves pulls against it. `MulticaAdapter` calls the sidecar service after each agent publish. Bootstrap no longer assigns skills globally.

**Tech Stack:** Python 3.11, PyYAML, pytest, multica CLI

---

### Task 1: Clean up skills/ and create catalog YAML structure

**Files:**
- Delete: `skills.txt`
- Create: `skills/skills.yaml`
- Create: `skills/components/shared/skills.yaml`
- Create: `skills/components/solution_architect/skills.yaml`
- Create: `skills/components/coding/skills.yaml`
- Create: `skills/components/qa/skills.yaml`
- Create: `skills/components/product/skills.yaml`
- Create: `skills/components/management/skills.yaml`
- Create: `skills/components/devops/skills.yaml`

- [ ] **Step 1: Remove existing skills/ content**

```bash
git submodule deinit -f skills/obsidian-wiki 2>/dev/null || true
git rm -f skills/obsidian-wiki 2>/dev/null || true
rm -rf skills/PRD skills/multica-collaboration skills/superpowers skills/vercel-react-best-practices
find skills/ -maxdepth 1 -type l -delete
git rm -f skills.txt
```

- [ ] **Step 2: Create `skills/skills.yaml`**

```yaml
version: 1

imports:
  - skills/components/solution_architect
  - skills/components/coding
  - skills/components/qa
  - skills/components/product
  - skills/components/management
  - skills/components/devops
  - skills/components/shared
```

- [ ] **Step 3: Create `skills/components/shared/skills.yaml`**

```yaml
version: 1
component: shared

repos:
  - name: multica-collaboration
    install: "https://github.com/HuyNguyenDinh/multica-collaboration-skill"
    skills:
      - multica-collaboration
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - using-superpowers
```

- [ ] **Step 4: Create `skills/components/solution_architect/skills.yaml`**

```yaml
version: 1
component: solution_architect

repos:
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - brainstorming
      - writing-plans
      - systematic-debugging
      - verification-before-completion
```

- [ ] **Step 5: Create `skills/components/coding/skills.yaml`**

```yaml
version: 1
component: coding

repos:
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - subagent-driven-development
      - executing-plans
      - test-driven-development
      - systematic-debugging
      - finishing-a-development-branch
      - using-git-worktrees
      - verification-before-completion
      - receiving-code-review
      - requesting-code-review
      - writing-skills
  - name: file-search
    install: "https://github.com/netresearch/file-search-skill"
    skills:
      - file-search
```

- [ ] **Step 6: Create `skills/components/qa/skills.yaml`**

```yaml
version: 1
component: qa

repos:
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - test-driven-development
      - systematic-debugging
      - verification-before-completion
      - receiving-code-review
```

- [ ] **Step 7: Create `skills/components/product/skills.yaml`**

```yaml
version: 1
component: product

repos:
  - name: awesome-copilot-prd
    install: "https://github.com/github/awesome-copilot --skill prd"
    skills:
      - prd
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - brainstorming
      - writing-plans
```

- [ ] **Step 8: Create `skills/components/management/skills.yaml`**

```yaml
version: 1
component: management

repos:
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - dispatching-parallel-agents
      - brainstorming
      - writing-plans
      - subagent-driven-development
```

- [ ] **Step 9: Create `skills/components/devops/skills.yaml`**

```yaml
version: 1
component: devops

repos:
  - name: superpowers
    install: "https://github.com/obra/superpowers"
    skills:
      - finishing-a-development-branch
      - using-git-worktrees
      - systematic-debugging
```

- [ ] **Step 10: Commit**

```bash
git add skills/
git commit -m "feat(skills): add centralized skills catalog with component registries"
```

---

### Task 2: SkillsCatalogService

**Files:**
- Create: `src/core/services/skills_catalog_service.py`
- Create: `tests/test_skills_catalog_service.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_skills_catalog_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_skills_catalog_service.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.core.services.skills_catalog_service'`

- [ ] **Step 3: Implement `SkillsCatalogService`**

Create `src/core/services/skills_catalog_service.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_skills_catalog_service.py -v
```
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/skills_catalog_service.py tests/test_skills_catalog_service.py
git commit -m "feat(skills): add SkillsCatalogService"
```

---

### Task 3: SkillsSidecarService

**Files:**
- Create: `src/core/services/skills_sidecar_service.py`
- Create: `tests/test_skills_sidecar_service.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_skills_sidecar_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_skills_sidecar_service.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.core.services.skills_sidecar_service'`

- [ ] **Step 3: Implement `SkillsSidecarService`**

Create `src/core/services/skills_sidecar_service.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_skills_sidecar_service.py -v
```
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/skills_sidecar_service.py tests/test_skills_sidecar_service.py
git commit -m "feat(skills): add SkillsSidecarService"
```

---

### Task 4: Create agent sidecar files

**Files:**
- Create: `agents/solution_architect/sa-agent.skills.yaml`
- Create: `agents/solution_architect/sa-critic-agent.skills.yaml`
- Create: `agents/coding/coder-agent.skills.yaml`
- Create: `agents/coding/code-planner-agent.skills.yaml`
- Create: `agents/coding/code-explorer-agent.skills.yaml`
- Create: `agents/coding/code-implementer-agent.skills.yaml`
- Create: `agents/coding/code-critic-agent.skills.yaml`
- Create: `agents/qa/qa-agent.skills.yaml`
- Create: `agents/qa/qa-critic-agent.skills.yaml`
- Create: `agents/product/product-manager-agent.skills.yaml`
- Create: `agents/product/product-lead-agent.skills.yaml`
- Create: `agents/product/product-critic-agent.skills.yaml`
- Create: `agents/management/pm-agent.skills.yaml`
- Create: `agents/devops/devops-agent.skills.yaml`

- [ ] **Step 1: Create solution_architect sidecars**

`agents/solution_architect/sa-agent.skills.yaml`:
```yaml
version: 1
agent: sa-agent

pull:
  - skills/components/solution_architect
  - skills/components/shared
```

`agents/solution_architect/sa-critic-agent.skills.yaml`:
```yaml
version: 1
agent: sa-critic-agent

pull:
  - skills/components/solution_architect
  - skills/components/shared
```

- [ ] **Step 2: Create coding sidecars**

`agents/coding/coder-agent.skills.yaml`:
```yaml
version: 1
agent: coder-agent

pull:
  - skills/components/coding
  - skills/components/shared
```

`agents/coding/code-planner-agent.skills.yaml`:
```yaml
version: 1
agent: code-planner-agent

pull:
  - skills/components/coding
  - skills/components/shared
```

`agents/coding/code-explorer-agent.skills.yaml`:
```yaml
version: 1
agent: code-explorer-agent

pull:
  - skills/components/coding
  - skills/components/shared
```

`agents/coding/code-implementer-agent.skills.yaml`:
```yaml
version: 1
agent: code-implementer-agent

pull:
  - skills/components/coding
  - skills/components/shared
```

`agents/coding/code-critic-agent.skills.yaml`:
```yaml
version: 1
agent: code-critic-agent

pull:
  - skills/components/coding
  - skills/components/shared
```

- [ ] **Step 3: Create qa sidecars**

`agents/qa/qa-agent.skills.yaml`:
```yaml
version: 1
agent: qa-agent

pull:
  - skills/components/qa
  - skills/components/shared
```

`agents/qa/qa-critic-agent.skills.yaml`:
```yaml
version: 1
agent: qa-critic-agent

pull:
  - skills/components/qa
  - skills/components/shared
```

- [ ] **Step 4: Create product sidecars**

`agents/product/product-manager-agent.skills.yaml`:
```yaml
version: 1
agent: product-manager-agent

pull:
  - skills/components/product
  - skills/components/shared
```

`agents/product/product-lead-agent.skills.yaml`:
```yaml
version: 1
agent: product-lead-agent

pull:
  - skills/components/product
  - skills/components/shared
```

`agents/product/product-critic-agent.skills.yaml`:
```yaml
version: 1
agent: product-critic-agent

pull:
  - skills/components/product
  - skills/components/shared
```

- [ ] **Step 5: Create management and devops sidecars**

`agents/management/pm-agent.skills.yaml`:
```yaml
version: 1
agent: pm-agent

pull:
  - skills/components/management
  - skills/components/shared
```

`agents/devops/devops-agent.skills.yaml`:
```yaml
version: 1
agent: devops-agent

pull:
  - skills/components/devops
  - skills/components/shared
```

- [ ] **Step 6: Commit**

```bash
git add agents/
git commit -m "feat(skills): add sidecar files for all agents"
```

---

### Task 5: Update install_skills.py to use catalog

**Files:**
- Modify: `src/install_skills.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
def test_install_skills_reads_from_catalog(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "skills.yaml").write_text(
        "version: 1\nimports:\n  - skills/components/shared\n"
    )
    shared_dir = skills_dir / "components" / "shared"
    shared_dir.mkdir(parents=True)
    (shared_dir / "skills.yaml").write_text(
        "version: 1\ncomponent: shared\nrepos:\n"
        "  - name: test-pkg\n    install: 'https://github.com/org/test'\n    skills: [skill-a]\n"
    )

    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        result = type("R", (), {"returncode": 0})()
        return result

    monkeypatch.setattr("src.install_skills.subprocess.run", fake_run)

    from src.install_skills import install_skills_from_catalog
    install_skills_from_catalog(project_root=tmp_path)

    assert any("https://github.com/org/test" in " ".join(c) for c in calls)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli.py -k "test_install_skills_reads_from_catalog" -v
```
Expected: FAIL — `cannot import name 'install_skills_from_catalog'`

- [ ] **Step 3: Add `install_skills_from_catalog` to `src/install_skills.py`**

Add after the existing imports at the top of `src/install_skills.py`:

```python
from src.core.services.skills_catalog_service import SkillsCatalogService
```

Add after the existing `install_skills_from_file` function:

```python
def install_skills_from_catalog(project_root: Path = PROJECT_ROOT, *, dry_run: bool = False) -> None:
    catalog = SkillsCatalogService(project_root=project_root)
    urls = catalog.get_install_urls()
    if not urls:
        print("No skills found in catalog")
        return

    if dry_run:
        print(f"[dry-run] Would install: {len(urls)} skill package(s)")
        for url in urls:
            print(f"  npx skills add {url} -y -g")
        return

    failed = 0
    for url in urls:
        print(f"Installing: {url}")
        parts = url.split()
        result = subprocess.run(["npx", "skills", "add", *parts, "-y", "-g"], capture_output=False, text=True)
        if result.returncode != 0:
            print(f"  ✗ Failed: {url}")
            failed += 1
        else:
            print(f"  ✓ Installed: {url}")

    if failed:
        raise RuntimeError(f"{failed} skill package(s) failed to install")

    print(f"\nAll {len(urls)} skill package(s) installed successfully")
```

Update `run()` to use the catalog when no `--file` flag is given:

```python
def run(args: argparse.Namespace) -> None:
    try:
        if getattr(args, "file", None):
            install_skills_from_file(Path(args.file), dry_run=args.dry_run)
        else:
            install_skills_from_catalog(dry_run=args.dry_run)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
```

Update `main()` to make `--file` optional:

```python
parser.add_argument(
    "--file", "-f",
    default=None,
    help="Path to legacy skills file (default: use skills/skills.yaml catalog)",
)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_cli.py -k "test_install_skills_reads_from_catalog" -v
```
Expected: PASS

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all existing tests pass

- [ ] **Step 6: Commit**

```bash
git add src/install_skills.py tests/test_cli.py
git commit -m "feat(skills): update install_skills to read from catalog"
```

---

### Task 6: Update MulticaAdapter to assign sidecar skills

**Files:**
- Modify: `src/adapters/multica_adapter.py`
- Modify: `tests/test_multica_adapter.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_multica_adapter.py`:

```python
from unittest.mock import MagicMock, patch
from src.core.services.skills_sidecar_service import SkillsSidecarService


def _make_adapter_with_sidecar(sidecar_svc):
    from src.adapters.multica_adapter import MulticaAdapter
    return MulticaAdapter(sidecar_service=sidecar_svc)


def _fake_agent():
    from src.core.domain.models import Agent
    return Agent(id="sa-agent", role="Solution Architect", instructions="do stuff")


def test_publish_agent_assigns_sidecar_skills_after_create():
    sidecar_svc = MagicMock(spec=SkillsSidecarService)
    sidecar_svc.has_sidecar.return_value = True
    sidecar_svc.get_skills_for_agent.return_value = ["brainstorming", "writing-plans"]

    adapter = _make_adapter_with_sidecar(sidecar_svc)

    def fake_run(args, **kw):
        res = MagicMock()
        res.returncode = 0
        if args[1:3] == ["agent", "list"]:
            res.stdout = "ID  NAME\n"
        elif args[1:3] == ["skill", "list"]:
            res.stdout = "ID  NAME\nid-1  brainstorming\nid-2  writing-plans\n"
        elif args[1:4] == ["agent", "skills", "set"]:
            res.stdout = ""
        else:
            res.stdout = ""
        return res

    with patch.object(adapter, "_run_cmd", side_effect=fake_run):
        result = adapter._publish_agent(_fake_agent())

    assert result is True
    sidecar_svc.has_sidecar.assert_called_once_with("sa-agent")
    sidecar_svc.get_skills_for_agent.assert_called_once_with("sa-agent")


def test_publish_agent_skips_skill_assignment_without_sidecar():
    sidecar_svc = MagicMock(spec=SkillsSidecarService)
    sidecar_svc.has_sidecar.return_value = False

    adapter = _make_adapter_with_sidecar(sidecar_svc)

    def fake_run(args, **kw):
        res = MagicMock()
        res.returncode = 0
        res.stdout = "ID  NAME\n"
        return res

    with patch.object(adapter, "_run_cmd", side_effect=fake_run):
        result = adapter._publish_agent(_fake_agent())

    assert result is True
    sidecar_svc.get_skills_for_agent.assert_not_called()


def test_publish_agent_fails_when_skill_ids_empty():
    sidecar_svc = MagicMock(spec=SkillsSidecarService)
    sidecar_svc.has_sidecar.return_value = True
    sidecar_svc.get_skills_for_agent.return_value = ["brainstorming"]

    adapter = _make_adapter_with_sidecar(sidecar_svc)

    def fake_run(args, **kw):
        res = MagicMock()
        res.returncode = 0
        # skill list returns nothing → no IDs resolved
        res.stdout = "ID  NAME\n" if args[1:3] == ["skill", "list"] else "ID  NAME\n"
        return res

    with patch.object(adapter, "_run_cmd", side_effect=fake_run):
        result = adapter._publish_agent(_fake_agent())

    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_multica_adapter.py -k "sidecar or skill" -v
```
Expected: FAIL — `MulticaAdapter.__init__` does not accept `sidecar_service`

- [ ] **Step 3: Update `MulticaAdapter`**

At the top of `src/adapters/multica_adapter.py`, add import:

```python
from src.core.services.skills_sidecar_service import SkillsSidecarService
```

Update `__init__`:

```python
def __init__(self, runtime_id: str = None, sidecar_service: SkillsSidecarService = None):
    self.runtime_id = runtime_id
    self._sidecar_service = sidecar_service
```

Add `_get_multica_skill_ids` method:

```python
def _get_multica_skill_ids(self, skill_names: list[str]) -> list[str]:
    res = self._run_cmd(["multica", "skill", "list"])
    if res.returncode != 0:
        return []
    name_to_id: dict[str, str] = {}
    for line in res.stdout.strip().splitlines()[1:]:
        parts = line.split(maxsplit=2)
        if len(parts) >= 2:
            name_to_id[parts[1]] = parts[0]
    return [name_to_id[n] for n in skill_names if n in name_to_id]
```

Add `_assign_sidecar_skills` method:

```python
def _assign_sidecar_skills(self, agent_id: str) -> bool:
    if not self._sidecar_service or not self._sidecar_service.has_sidecar(agent_id):
        return True

    skill_names = self._sidecar_service.get_skills_for_agent(agent_id)
    skill_ids = self._get_multica_skill_ids(skill_names)

    if not skill_ids:
        print(f"  ✗ No Multica skill IDs resolved for '{agent_id}'", file=sys.stderr)
        return False

    agent_uuid = self._get_agent_uuid(agent_id)
    res = self._run_cmd([
        "multica", "agent", "skills", "set", agent_uuid,
        "--skill-ids", ",".join(skill_ids),
    ])
    if res.returncode != 0:
        print(f"  ✗ Failed to assign skills to '{agent_id}': {res.stderr.strip()}", file=sys.stderr)
        return False
    print(f"  ✓ Assigned {len(skill_ids)} skill(s) to '{agent_id}'")
    return True
```

In `_publish_agent`, replace the final `return True` with:

```python
    print(f"  ✓ Successfully synced '{agent.id}'")
    return self._assign_sidecar_skills(agent.id)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_multica_adapter.py -v
```
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/multica_adapter.py tests/test_multica_adapter.py
git commit -m "feat(skills): MulticaAdapter assigns sidecar skills after agent publish"
```

---

### Task 7: Remove global assignment from bootstrap_multica_skills.py

**Files:**
- Modify: `src/bootstrap_multica_skills.py`
- Create: `tests/test_bootstrap_multica_skills.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_bootstrap_multica_skills.py`:

```python
from unittest.mock import patch, MagicMock
from src import bootstrap_multica_skills as bms


def test_run_does_not_assign_skills_globally():
    with patch.object(bms, "sync_skills_to_multica", return_value=["id-1"]), \
         patch.object(bms, "assign_skills_to_all_agents") as mock_assign:
        args = MagicMock()
        args.dry_run = False
        bms.run(args)

    mock_assign.assert_not_called()


def test_sync_skills_filters_by_catalog(tmp_path):
    from src.core.services.skills_catalog_service import SkillsCatalogService

    fake_catalog = MagicMock(spec=SkillsCatalogService)
    fake_catalog.get_all_skills.return_value = {"shared": ["multica-collaboration"]}

    with patch("src.bootstrap_multica_skills.SkillsCatalogService", return_value=fake_catalog), \
         patch("src.bootstrap_multica_skills.get_local_skills", return_value={}):
        result = bms.sync_skills_to_multica(dry_run=True)

    fake_catalog.get_all_skills.assert_called_once()
    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_bootstrap_multica_skills.py -v
```
Expected: `test_run_does_not_assign_skills_globally` FAIL (assign is still called in `run`)

- [ ] **Step 3: Update `bootstrap_multica_skills.py`**

Add import at the top (after existing imports):

```python
from src.core.services.skills_catalog_service import SkillsCatalogService
```

Remove the `CORE_SKILLS` list entirely.

Replace the filter logic in `sync_skills_to_multica`:

```python
def sync_skills_to_multica(*, dry_run: bool = False) -> list[str]:
    local = get_local_skills()
    if not local:
        print("No local skills found in", SKILLS_DIR)
        return []

    catalog = SkillsCatalogService()
    catalog_skills: set[str] = {
        s for skills in catalog.get_all_skills().values() for s in skills
    }

    print(f"Syncing skills from {SKILLS_DIR} to Multica workspace...")
    skill_ids: list[str] = []
    failed = 0

    for name, path in local.items():
        if name not in catalog_skills:
            continue
        sid = create_or_update_skill(name, path, dry_run=dry_run)
        if sid:
            skill_ids.append(sid)
        elif not dry_run:
            failed += 1

    total = len([n for n in local if n in catalog_skills])
    print(f"\nSkills: {len(skill_ids)}/{total} synced" + (f", {failed} failed" if failed else ""))
    return skill_ids
```

Replace `run()`:

```python
def run(args) -> None:
    dry_run = getattr(args, "dry_run", False)
    sync_skills_to_multica(dry_run=dry_run)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_bootstrap_multica_skills.py -v
```
Expected: 2 tests PASS

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/bootstrap_multica_skills.py tests/test_bootstrap_multica_skills.py
git commit -m "feat(skills): remove global skill assignment; bootstrap filters by catalog"
```

---

## Verification

Spot-check sidecar resolution works end-to-end:

```bash
python -c "
from src.core.services.skills_catalog_service import SkillsCatalogService
from src.core.services.skills_sidecar_service import SkillsSidecarService
from pathlib import Path
catalog = SkillsCatalogService()
svc = SkillsSidecarService(catalog=catalog, agents_root=Path('agents'))
print('sa-agent:', svc.get_skills_for_agent('sa-agent'))
print('coder-agent:', svc.get_skills_for_agent('coder-agent'))
print('pm-agent:', svc.get_skills_for_agent('pm-agent'))
"
```

Expected: each agent prints its component skills plus shared skills, with no overlap from other components.

Dry-run bootstrap to confirm no global assignment:

```bash
python -m src.cli bootstrap --dry-run
```

Expected: per-agent `[dry-run] multica agent skills set` lines only for agents with sidecars. No bulk "assign all to all agents" line.

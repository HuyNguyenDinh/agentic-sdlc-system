#!/usr/bin/env python3
"""Bootstrap skills from local ~/.agents/skills/ into the Multica workspace.

Reads all SKILL.md files from the local skills directory, creates/updates them
in Multica via `multica skill create`. Per-agent skill assignment is handled
separately by MulticaAdapter._assign_sidecar_skills() during sync-agent.
"""

import json
import subprocess
import sys
from pathlib import Path

from src.core.services.skills_catalog_service import SkillsCatalogService

SKILLS_DIR = Path.home() / ".agents" / "skills"


def _run_cmd(args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, check=False, timeout=timeout)
    except FileNotFoundError:
        res = subprocess.CompletedProcess(args, returncode=127)
        res.stderr = "multica: command not found"
        return res
    except subprocess.TimeoutExpired:
        res = subprocess.CompletedProcess(args, returncode=124)
        res.stderr = "Command timed out"
        return res


def get_local_skills() -> dict[str, Path]:
    """Scan ~/.agents/skills/ and return {name: SKILL.md path}."""
    skills = {}
    if not SKILLS_DIR.is_dir():
        return skills
    for entry in sorted(SKILLS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.is_file():
            skills[entry.name] = skill_md
    return skills


def get_multica_skills() -> dict[str, str]:
    """Return {name: id} for all skills currently in the Multica workspace."""
    res = _run_cmd(["multica", "skill", "list"])
    if res.returncode != 0:
        return {}
    skills = {}
    lines = res.stdout.strip().splitlines()
    if len(lines) <= 1:
        return skills
    for line in lines[1:]:
        parts = line.split(maxsplit=3)
        if len(parts) >= 2:
            skills[parts[1]] = parts[0]
    return skills


def create_or_update_skill(name: str, skill_md_path: Path, *, dry_run: bool = False) -> str | None:
    """Create (or update) a skill in Multica from local SKILL.md. Returns skill ID."""
    existing = get_multica_skills()

    if name in existing:
        skill_id = existing[name]

        if dry_run:
            print(f"  [dry-run] skill update {skill_id} --name {name}")
            return skill_id

        # Update: use skill update --config + --content-file
        config_json = json.dumps({"name": name})
        res = _run_cmd([
            "multica", "skill", "update", skill_id,
            "--config", config_json,
            "--content-file", str(skill_md_path.resolve()),
        ])
        if res.returncode != 0:
            print(f"  ✗ Failed to update skill '{name}': {res.stderr.strip()}", file=sys.stderr)
            return None
        print(f"  ✓ Updated skill '{name}' ({skill_id})")
        return skill_id
    else:
        # Create new skill
        desc_line = skill_md_path.read_text().splitlines()[0] if skill_md_path.exists() else ""
        desc = desc_line.strip().lstrip("# ")[:200] if desc_line else name

        if dry_run:
            print(f"  [dry-run] multica skill create --name {name} --description <short> --content-file <path>")
            return None

        res = _run_cmd([
            "multica", "skill", "create",
            "--name", name,
            "--description", desc,
            "--content-file", str(skill_md_path.resolve()),
        ])
        if res.returncode != 0:
            err = res.stderr.strip()
            if "already exists" in err:
                # Race condition — someone else created it. Fetch ID.
                refreshed = get_multica_skills()
                rid = refreshed.get(name)
                if rid:
                    print(f"  ✓ Skill '{name}' already exists ({rid})")
                    return rid
            print(f"  ✗ Failed to create skill '{name}': {err}", file=sys.stderr)
            return None
        try:
            data = json.loads(res.stdout)
            skill_id = data.get("id", "")
            print(f"  ✓ Created skill '{name}' ({skill_id})")
            return skill_id
        except (json.JSONDecodeError, KeyError):
            print(f"  ✓ Created skill '{name}' (ID in output)")
            return None


def sync_skills_to_multica(*, dry_run: bool = False, catalog: SkillsCatalogService = None) -> list[str]:
    """Import local skills into Multica workspace. Returns list of skill IDs.

    If catalog is provided, only skills whose names appear in the catalog are
    synced. If no catalog is given, all local skills are synced.
    """
    local = get_local_skills()
    if not local:
        print("No local skills found in", SKILLS_DIR)
        return []

    # Build allowed set from catalog; empty set means "no filter"
    allowed_names: set[str] = set()
    if catalog is not None:
        for skills in catalog.get_all_skills().values():
            allowed_names.update(skills)

    print(f"Syncing skills from {SKILLS_DIR} to Multica workspace...")

    skill_ids: list[str] = []
    failed = 0

    for name, path in local.items():
        if allowed_names and name not in allowed_names:
            continue

        sid = create_or_update_skill(name, path, dry_run=dry_run)
        if sid:
            skill_ids.append(sid)
        elif not dry_run:
            failed += 1

    total = len([n for n in local if not allowed_names or n in allowed_names])
    print(f"\nSkills: {len(skill_ids)}/{total} synced" + (f", {failed} failed" if failed else ""))
    return skill_ids


def run(args) -> None:
    """Main entrypoint for the CLI command."""
    dry_run = getattr(args, "dry_run", False)

    catalog = SkillsCatalogService()
    skill_ids = sync_skills_to_multica(catalog=catalog, dry_run=dry_run)
    if not skill_ids:
        if not dry_run:
            print("No skills to assign. Check that local skills exist and are importable.")
        return


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bootstrap skills from local filesystem to Multica workspace")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Print actions without executing")
    args = parser.parse_args()
    run(args)

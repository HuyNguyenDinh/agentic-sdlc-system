#!/usr/bin/env python3
"""Bootstrap skills from local ~/.agents/skills/ into the Multica workspace.

Reads all SKILL.md files from the local skills directory, creates/updates them
in Multica via `multica skill create`, and optionally assigns them to agents.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

SKILLS_DIR = Path.home() / ".agents" / "skills"

# Skills needed by development agents for wiki/KB management
# (all skills get assigned to all agents anyway, but this defines the set)
CORE_SKILLS = [
    # Wiki / KB
    "llm-wiki", "obsidian", "obsidian-wiki-ingest",
    "wiki-agent", "wiki-capture", "wiki-context-pack", "wiki-dashboard",
    "wiki-dedup", "wiki-digest", "wiki-export", "wiki-history-ingest",
    "wiki-import", "wiki-ingest", "wiki-lint", "wiki-query",
    "wiki-quick-chat-capture", "wiki-rebuild", "wiki-research",
    "wiki-setup", "wiki-stage-commit", "wiki-status", "wiki-switch",
    "wiki-synthesize", "wiki-update",
    # Development workflow
    "brainstorming", "dispatching-parallel-agents", "executing-plans",
    "finishing-a-development-branch", "multica-collaboration", "prd",
    "receiving-code-review", "requesting-code-review",
    "subagent-driven-development", "systematic-debugging",
    "test-driven-development", "using-git-worktrees", "using-superpowers",
    "verification-before-completion", "writing-plans", "writing-skills",
    # Tools
    "todoist", "cross-linker", "tag-taxonomy", "graph-colorize",
    "data-ingest", "ingest-url", "daily-update", "memory-bridge",
    # Research
    "arxiv", "blogwatcher", "llm-wiki", "polymarket",
    # Media
    "gif-search", "heartmula", "songsee", "youtube-content",
    # GitHub
    "github-auth", "github-code-review", "github-issues",
    "github-pr-workflow", "github-repo-management",
    "codebase-inspection",
]


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


def create_or_update_skill(name: str, skill_md_path: Path, *, dry_run: bool = False) -> Optional[str]:
    """Create (or update) a skill in Multica from local SKILL.md. Returns skill ID."""
    existing = get_multica_skills()
    
    if name in existing:
        skill_id = existing[name]
        desc_line = skill_md_path.read_text().splitlines()[0] if skill_md_path.exists() else ""
        desc = desc_line.strip().lstrip("# ")[:200] if desc_line else name
        
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


def get_all_agent_ids() -> list[tuple[str, str]]:
    """Return [(agent_id, agent_name)] for all agents in the current workspace."""
    res = _run_cmd(["multica", "agent", "list"])
    if res.returncode != 0:
        print(f"  ⚠ Failed to list agents: {res.stderr.strip()}", file=sys.stderr)
        return []
    agents = []
    for line in res.stdout.strip().splitlines()[1:]:
        parts = line.split(maxsplit=3)
        if len(parts) >= 2:
            agents.append((parts[0], parts[1]))
    return agents


def assign_skills_to_agent(agent_id: str, agent_name: str, skill_ids: list[str], *, dry_run: bool = False) -> bool:
    """Assign all skills to a single agent via multica agent skills set."""
    if not skill_ids:
        return True
    
    if dry_run:
        print(f"  [dry-run] multica agent skills set {agent_id} --skill-ids <{len(skill_ids)} skills>")
        return True
    
    res = _run_cmd([
        "multica", "agent", "skills", "set", agent_id,
        "--skill-ids", ",".join(skill_ids),
    ])
    if res.returncode != 0:
        print(f"  ✗ Failed to assign skills to '{agent_name}' ({agent_id[:8]}...): {res.stderr.strip()}", file=sys.stderr)
        return False
    print(f"  ✓ Assigned {len(skill_ids)} skills to '{agent_name}'")
    return True


def sync_skills_to_multica(*, dry_run: bool = False) -> list[str]:
    """Import all local skills into Multica workspace. Returns list of skill IDs."""
    local = get_local_skills()
    if not local:
        print("No local skills found in", SKILLS_DIR)
        return []
    
    print(f"Syncing {len(local)} skills from {SKILLS_DIR} to Multica workspace...")
    
    skill_ids: list[str] = []
    failed = 0
    
    for i, (name, path) in enumerate(local.items(), 1):
        skip = False
        # Only import skills that are in our CORE_SKILLS list (skip generic/personal stuff)
        if name not in CORE_SKILLS:
            skip = True
            continue
            
        sid = create_or_update_skill(name, path, dry_run=dry_run)
        if sid:
            skill_ids.append(sid)
        elif not dry_run:
            failed += 1
    
    total = len([n for n in local if n in CORE_SKILLS])
    print(f"\nSkills: {len(skill_ids)}/{total} synced" + (f", {failed} failed" if failed else ""))
    return skill_ids


def assign_skills_to_all_agents(skill_ids: list[str], *, dry_run: bool = False) -> bool:
    """Assign list of skill IDs to every agent in the workspace."""
    agents = get_all_agent_ids()
    if not agents:
        print("No agents found in workspace")
        return False
    
    print(f"\nAssigning {len(skill_ids)} skill(s) to {len(agents)} agent(s)...")
    
    failed = 0
    for agent_id, agent_name in agents:
        if not assign_skills_to_agent(agent_id, agent_name, skill_ids, dry_run=dry_run):
            failed += 1
    
    success = len(agents) - failed
    print(f"\nAgents: {success}/{len(agents)} assigned" + (f", {failed} failed" if failed else ""))
    return failed == 0


def run(args) -> None:
    """Main entrypoint for the CLI command."""
    dry_run = getattr(args, "dry_run", False)
    
    skill_ids = sync_skills_to_multica(dry_run=dry_run)
    if not skill_ids:
        if not dry_run:
            print("No skills to assign. Check that local skills exist and are importable.")
        return
    
    assign_skills_to_all_agents(skill_ids, dry_run=dry_run)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bootstrap skills from local filesystem to Multica workspace")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Print actions without executing")
    args = parser.parse_args()
    run(args)

#!/usr/bin/env python3
"""Bootstrap GitNexus runtime integration for codebase knowledge analysis."""

from __future__ import annotations

import argparse
import tempfile
import re
import subprocess
from pathlib import Path


def normalize_repo_input(repo: str) -> str:
    """Normalize GitHub repo input into owner/repo format."""
    value = repo.strip()
    if not value:
        raise ValueError("Repository cannot be empty")

    value = re.sub(r"\.git$", "", value)

    https_match = re.match(r"^https://github\.com/([^/]+)/([^/]+)$", value)
    ssh_match = re.match(r"^git@github\.com:([^/]+)/([^/]+)$", value)
    slug_match = re.match(r"^([^/\s]+)/([^/\s]+)$", value)

    if https_match:
        return f"{https_match.group(1)}/{https_match.group(2)}"
    if ssh_match:
        return f"{ssh_match.group(1)}/{ssh_match.group(2)}"
    if slug_match:
        return value

    raise ValueError("Unsupported repo format. Use owner/repo or a GitHub URL")


def build_gitnexus_install_command() -> list[str]:
    """Build npm install command for GitNexus."""
    return ["npm", "install", "-g", "gitnexus"]


def install_gitnexus(*, dry_run: bool = False) -> None:
    """Install GitNexus globally without running repository analysis."""
    _run(build_gitnexus_install_command(), dry_run=dry_run)


def build_analyze_command(repo: str) -> list[str]:
    """Build analyze command for a single repository."""
    return ["npx", "gitnexus", "analyze", repo]


def build_clone_command(repo_slug: str, destination: str) -> list[str]:
    """Build git clone command for a GitHub repository."""
    return ["git", "clone", f"https://github.com/{repo_slug}.git", destination]


def _run(command: list[str], cwd: str | None = None, dry_run: bool = False) -> None:
    """Execute a command or print it if dry_run is True."""
    if dry_run:
        print(f"[dry-run] {' '.join(command)}")
        return

    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or "no output"
        raise RuntimeError(f"Command failed ({' '.join(command)}): {details}")


def _resolve_repo_worktree(repo_input: str, *, dry_run: bool = False) -> tuple[str, tempfile.TemporaryDirectory[str] | None]:
    """Return a local git worktree path for the repository input.

    Local paths are used as-is. GitHub URLs or owner/repo slugs are cloned into a
    temporary checkout so GitNexus can analyze a real git repository.
    """
    local_path = Path(repo_input).expanduser()
    if local_path.exists():
        if not local_path.is_dir():
            raise RuntimeError(f"Repository path is not a directory: {local_path}")
        return str(local_path.resolve()), None

    repo_slug = normalize_repo_input(repo_input)
    temp_dir = tempfile.TemporaryDirectory(prefix="gitnexus-")
    checkout_path = Path(temp_dir.name) / repo_slug.split("/")[-1]

    _run(build_clone_command(repo_slug, str(checkout_path)), dry_run=dry_run)
    return str(checkout_path), temp_dir


def run_bootstrap(args: argparse.Namespace) -> None:
    """Execute the GitNexus bootstrap workflow."""
    mode = args.mode
    repos = args.repos or []
    repo = args.repo

    if mode == "monorepo" and not repo:
        raise RuntimeError("--repo is required for monorepo mode")
    if mode == "multi-repo" and not repos:
        raise RuntimeError("--repos is required for multi-repo mode")

    install_gitnexus(dry_run=args.dry_run)

    if mode == "monorepo":
        worktree, temp_dir = _resolve_repo_worktree(repo, dry_run=args.dry_run)
        try:
            _run(build_analyze_command(worktree), cwd=worktree, dry_run=args.dry_run)
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()
        return

    group_name = args.group_name or "gitnexus-group"
    _run(["npx", "gitnexus", "group", "create", group_name], dry_run=args.dry_run)
    for repo_value in repos:
        worktree, temp_dir = _resolve_repo_worktree(repo_value, dry_run=args.dry_run)
        try:
            _run(build_analyze_command(worktree), cwd=worktree, dry_run=args.dry_run)
            _run(["npx", "gitnexus", "group", "attach", group_name, worktree], dry_run=args.dry_run)
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()
    _run(["npx", "gitnexus", "group", "sync", group_name], dry_run=args.dry_run)


def build_parser(subparsers) -> None:
    """Build the bootstrap-gitnexus subcommand parser."""
    parser = subparsers.add_parser("bootstrap-gitnexus", help="bootstrap GitNexus runtime and analysis flow")
    parser.add_argument("--mode", choices=["monorepo", "multi-repo"], required=True, help="working mode")
    parser.add_argument("--repo", help="monorepo input (owner/repo or URL)")
    parser.add_argument("--repos", nargs="*", help="multi-repo inputs (owner/repo or URL)")
    parser.add_argument("--group-name", help="GitNexus group name for multi-repo mode")
    parser.add_argument("--dry-run", action="store_true", help="print actions without executing them")
    parser.set_defaults(func=run_bootstrap)

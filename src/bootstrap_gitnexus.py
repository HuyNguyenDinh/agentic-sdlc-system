#!/usr/bin/env python3
"""Bootstrap GitNexus runtime integration for codebase knowledge analysis."""

from __future__ import annotations

import argparse
import re
import subprocess


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


def build_analyze_command(repo: str) -> list[str]:
    """Build analyze command for a single repository."""
    return ["npx", "gitnexus", "analyze", repo]


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


def run_bootstrap(args: argparse.Namespace) -> None:
    """Execute the GitNexus bootstrap workflow."""
    mode = args.mode
    repos = args.repos or []
    repo = args.repo

    if mode == "single" and not repo:
        raise RuntimeError("--repo is required for single mode")
    if mode == "multi" and not repos:
        raise RuntimeError("--repos is required for multi mode")

    _run(build_gitnexus_install_command(), dry_run=args.dry_run)

    if mode == "single":
        resolved = normalize_repo_input(repo)
        _run(build_analyze_command(resolved), dry_run=args.dry_run)
        return

    group_name = args.group_name or "gitnexus-group"
    _run(["npx", "gitnexus", "group", "create", group_name], dry_run=args.dry_run)
    for repo_value in repos:
        resolved = normalize_repo_input(repo_value)
        _run(["npx", "gitnexus", "repo", "pull", resolved], dry_run=args.dry_run)
        _run(build_analyze_command(resolved), dry_run=args.dry_run)
        _run(["npx", "gitnexus", "group", "attach", group_name, resolved], dry_run=args.dry_run)
    _run(["npx", "gitnexus", "group", "sync", group_name], dry_run=args.dry_run)


def build_parser(subparsers) -> None:
    """Build the bootstrap-gitnexus subcommand parser."""
    parser = subparsers.add_parser("bootstrap-gitnexus", help="bootstrap GitNexus runtime and analysis flow")
    parser.add_argument("--mode", choices=["single", "multi"], required=True, help="working mode")
    parser.add_argument("--repo", help="single repository input (owner/repo or URL)")
    parser.add_argument("--repos", nargs="*", help="multi-repo inputs (owner/repo or URL)")
    parser.add_argument("--group-name", help="GitNexus group name for multi mode")
    parser.add_argument("--dry-run", action="store_true", help="print actions without executing them")
    parser.set_defaults(func=run_bootstrap)

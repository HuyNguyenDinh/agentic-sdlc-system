#!/usr/bin/env python3
"""Bootstrap Obsidian Wiki runtime integration for agent knowledge base usage."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_VAULT_PATH = str(Path.home() / "obsidian-wiki")
DEFAULT_BRANCH = "main"
OBSIDIAN_WIKI_INSTALL_REPO = "https://github.com/Ar9av/obsidian-wiki.git"


def normalize_repo_identifier(repo: str) -> str:
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

    raise ValueError(
        "Unsupported repo format. Use owner/repo or a GitHub URL like https://github.com/owner/repo"
    )


def build_cron_line(vault_path: str, branch: str) -> str:
    """Build the managed cron line for periodic wiki sync."""
    return (
        "*/5 * * * * "
        f"cd {vault_path} && git add . && git commit -m \"automated backup commit\" && git push origin {branch}"
    )


def merge_crontab(existing_content: str, managed_line: str) -> str:
    """Insert managed line if absent while avoiding duplicates."""
    lines = [line for line in existing_content.splitlines() if line.strip()]
    lines = [line for line in lines if line.strip() != managed_line.strip()]
    lines.append(managed_line)
    return "\n".join(lines) + "\n"


def upsert_export_line(existing_content: str, key: str, value: str) -> str:
    """Insert or replace environment export entry in shell profile content."""
    export_line = f'export {key}="{value}"'
    out: list[str] = []
    replaced = False

    for line in existing_content.splitlines():
        if line.strip().startswith(f"export {key}="):
            if not replaced:
                out.append(export_line)
                replaced = True
            continue
        out.append(line)

    if not replaced:
        if out and out[-1].strip() != "":
            out.append("")
        out.append(export_line)

    return "\n".join(out).rstrip() + "\n"


def _run(command: list[str], *, cwd: str | None = None, env: dict[str, str] | None = None, dry_run: bool = False) -> None:
    cmd_text = " ".join(command)
    if dry_run:
        print(f"[dry-run] {cmd_text}")
        return

    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or "no output"
        raise RuntimeError(f"Command failed ({cmd_text}): {details}")


def _require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found: {name}")


def _ensure_gh_auth(*, dry_run: bool = False) -> None:
    if dry_run:
        print("[dry-run] gh auth status")
        return
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("GitHub CLI is not authenticated. Run: gh auth login")


def _sync_repo(repo_slug: str, vault_path: Path, branch: str, force: bool, dry_run: bool) -> None:
    if not vault_path.exists():
        if not dry_run:
            vault_path.parent.mkdir(parents=True, exist_ok=True)
        _run(["gh", "repo", "clone", repo_slug, str(vault_path)], dry_run=dry_run)
    elif not (vault_path / ".git").exists():
        if not force:
            raise RuntimeError(f"Vault path exists but is not a git repository: {vault_path}")
        raise RuntimeError("Force overwrite for non-git directories is not supported automatically")

    _run(["git", "fetch", "origin"], cwd=str(vault_path), dry_run=dry_run)
    _run(["git", "checkout", branch], cwd=str(vault_path), dry_run=dry_run)
    _run(["git", "pull", "--rebase", "origin", branch], cwd=str(vault_path), dry_run=dry_run)


def _install_obsidian_wiki(vault_path: str, *, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[dry-run] git clone {OBSIDIAN_WIKI_INSTALL_REPO}")
        print(f"[dry-run] write .env with OBSIDIAN_VAULT_PATH={vault_path}")
        print(f"[dry-run] OBSIDIAN_VAULT_PATH={vault_path} bash setup.sh")
        print(f"[dry-run] obsidian-wiki setup --vault {vault_path}")
        return

    with tempfile.TemporaryDirectory(prefix="obsidian-wiki-install-") as tmp_dir:
        install_root = Path(tmp_dir)
        repo_dir = install_root / "obsidian-wiki"
        _run(["git", "clone", OBSIDIAN_WIKI_INSTALL_REPO, str(repo_dir)])

        repo_env = repo_dir / ".env"
        repo_env.write_text(f'OBSIDIAN_VAULT_PATH="{vault_path}"\n')

        try:
            _run(
                ["env", f"OBSIDIAN_VAULT_PATH={vault_path}", "bash", "setup.sh"],
                cwd=str(repo_dir),
            )

            _run(
                ["obsidian-wiki", "setup", "--vault", vault_path],
                env={"OBSIDIAN_VAULT_PATH": vault_path, **os.environ},
            )
        finally:
            shutil.rmtree(repo_dir, ignore_errors=True)


def _persist_env(vault_path: str, *, dry_run: bool = False) -> None:
    profile = Path.home() / ".profile"
    existing = ""
    if profile.exists():
        existing = profile.read_text()

    updated = upsert_export_line(existing, "OBSIDIAN_VAULT_PATH", vault_path)

    if dry_run:
        print(f"[dry-run] update {profile} with OBSIDIAN_VAULT_PATH={vault_path}")
    else:
        profile.write_text(updated)

    os.environ["OBSIDIAN_VAULT_PATH"] = vault_path


def _install_cron(vault_path: str, branch: str, *, dry_run: bool = False) -> str:
    managed = build_cron_line(vault_path, branch)

    if dry_run:
        print("[dry-run] crontab -l")
        print(f"[dry-run] install cron: {managed}")
        return managed

    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    existing = current.stdout if current.returncode == 0 else ""

    merged = merge_crontab(existing, managed)
    apply_result = subprocess.run(["crontab", "-"], input=merged, text=True, capture_output=True)
    if apply_result.returncode != 0:
        details = apply_result.stderr.strip() or apply_result.stdout.strip() or "no output"
        raise RuntimeError(f"Failed to install crontab entry: {details}")

    return managed


def _read_current_crontab() -> str:
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if current.returncode != 0:
        return ""
    return current.stdout


def _read_profile_export(key: str) -> str | None:
    profile = Path.home() / ".profile"
    if not profile.exists():
        return None

    for line in profile.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith(f"export {key}="):
            value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            return value
    return None


def _get_origin_repo_slug(vault_path: Path) -> str | None:
    if not (vault_path / ".git").exists():
        return None

    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(vault_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    url = result.stdout.strip()
    if not url:
        return None

    try:
        return normalize_repo_identifier(url)
    except ValueError:
        return None


def run_bootstrap(args: argparse.Namespace) -> None:
    repo_value = args.repo
    if not repo_value and not args.non_interactive:
        repo_value = input("Enter private GitHub repository (owner/repo or URL): ").strip()

    if not repo_value:
        raise RuntimeError("Repository is required. Provide --repo in non-interactive mode.")

    repo_slug = normalize_repo_identifier(repo_value)
    vault_path = Path(args.vault_path).expanduser()
    branch = args.branch

    _require_command("gh")
    _require_command("git")
    _require_command("crontab")
    _ensure_gh_auth(dry_run=args.dry_run)

    _sync_repo(repo_slug, vault_path, branch, args.force, args.dry_run)
    _install_obsidian_wiki(str(vault_path), dry_run=args.dry_run)
    _persist_env(str(vault_path), dry_run=args.dry_run)
    cron_line = _install_cron(str(vault_path), branch, dry_run=args.dry_run)

    print("Obsidian Wiki bootstrap complete")
    print(f"Repository: {repo_slug}")
    print(f"Vault path: {vault_path}")
    print(f"Cron sync: {cron_line}")


def run_post_bootstrap_check(args: argparse.Namespace) -> None:
    vault_path = Path(args.vault_path)
    branch = args.branch
    expected_repo_slug = normalize_repo_identifier(args.repo) if args.repo else None
    expected_cron = build_cron_line(str(vault_path), branch)

    failures: list[str] = []

    if (vault_path / ".git").exists():
        print(f"OK vault git repo: {vault_path}")
    else:
        failures.append(f"Vault is missing or not a git repository: {vault_path}")

    profile_vault = _read_profile_export("OBSIDIAN_VAULT_PATH")
    if profile_vault == str(vault_path):
        print(f"OK OBSIDIAN_VAULT_PATH in profile: {profile_vault}")
    else:
        failures.append(
            "OBSIDIAN_VAULT_PATH in ~/.profile does not match expected path "
            f"({str(vault_path)}). Found: {profile_vault!r}"
        )

    crontab_content = _read_current_crontab()
    if expected_cron in crontab_content:
        print("OK cron sync entry is installed")
    else:
        failures.append("Managed cron sync entry was not found in crontab")

    origin_slug = _get_origin_repo_slug(vault_path)
    if origin_slug:
        print(f"OK git origin repo: {origin_slug}")
        if expected_repo_slug and origin_slug != expected_repo_slug:
            failures.append(
                f"git origin mismatch. Expected {expected_repo_slug}, found {origin_slug}"
            )
    else:
        failures.append("Unable to resolve git origin remote repository")

    if failures:
        raise RuntimeError("; ".join(failures))

    print("Post-bootstrap verification complete")


def build_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "bootstrap-wiki",
        help="bootstrap obsidian-wiki runtime with git sync cron",
    )
    parser.add_argument("--repo", help="private GitHub repository (owner/repo or URL)")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help=f"git branch to sync (default: {DEFAULT_BRANCH})")
    parser.add_argument("--vault-path", default=DEFAULT_VAULT_PATH, help=f"vault path (default: {DEFAULT_VAULT_PATH})")
    parser.add_argument("--non-interactive", action="store_true", help="fail instead of prompting when --repo is missing")
    parser.add_argument("--force", action="store_true", help="allow unsafe operations where supported")
    parser.add_argument("--dry-run", action="store_true", help="print actions without changing the system")


def build_check_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "check-wiki-bootstrap",
        help="verify obsidian-wiki cron, env var, and git remote setup",
    )
    parser.add_argument("--repo", help="expected private GitHub repository (owner/repo or URL)")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help=f"git branch in cron sync (default: {DEFAULT_BRANCH})")
    parser.add_argument("--vault-path", default=DEFAULT_VAULT_PATH, help=f"vault path (default: {DEFAULT_VAULT_PATH})")

#!/usr/bin/env python3
"""Install skills from skills.txt using the skills.sh CLI."""

import argparse
import subprocess
import sys
from pathlib import Path

from src.core.services.skills_catalog_service import SkillsCatalogService

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILLS_FILE = PROJECT_ROOT / "skills.txt"


def parse_skills(path: Path) -> list[str]:
    lines: list[str] = []
    with open(path) as f:
        for raw in f:
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lines.append(stripped)
    return lines


def install_skills_from_file(skills_file: Path, *, dry_run: bool = False) -> None:
    if not skills_file.exists():
        raise RuntimeError(f"{skills_file} not found")

    skills = parse_skills(skills_file)
    if not skills:
        print("No skills found in", skills_file)
        return

    if dry_run:
        print("[dry-run] Would install:", len(skills), "skill(s)")
        for s in skills:
            print(f"  npx skills add {s} -y -g")
        return

    failed = 0
    for s in skills:
        print(f"Installing: {s}")
        parts = s.split()
        cmd = ["npx", "skills", "add", *parts, "-y", "-g"]
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
        )
        if result.returncode != 0:
            print(f"  ✗ Failed: {s}")
            failed += 1
        else:
            print(f"  ✓ Installed: {s}")

    if failed:
        raise RuntimeError(f"{failed} skill(s) failed to install")

    print(f"\nAll {len(skills)} skill(s) installed successfully")


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


def run(args: argparse.Namespace) -> None:
    try:
        if getattr(args, "file", None):
            install_skills_from_file(Path(args.file), dry_run=args.dry_run)
        else:
            install_skills_from_catalog(dry_run=args.dry_run)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Install skills from skills.txt using the skills.sh CLI"
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Path to legacy skills file (default: use skills/skills.yaml catalog)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print what would be installed without executing",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

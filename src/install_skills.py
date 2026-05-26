#!/usr/bin/env python3
"""Install skills from skills.txt using the skills.sh CLI."""

import argparse
import subprocess
import sys
from pathlib import Path

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


def run(args: argparse.Namespace) -> None:
    skills_file = Path(args.file)

    if not skills_file.exists():
        print(f"Error: {skills_file} not found")
        sys.exit(1)

    skills = parse_skills(skills_file)
    if not skills:
        print("No skills found in", skills_file)
        return

    if args.dry_run:
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
        print(f"\n{failed} skill(s) failed to install")
        sys.exit(1)
    else:
        print(f"\nAll {len(skills)} skill(s) installed successfully")


def main():
    parser = argparse.ArgumentParser(
        description="Install skills from skills.txt using the skills.sh CLI"
    )
    parser.add_argument(
        "--file", "-f",
        default=str(DEFAULT_SKILLS_FILE),
        help=f"Path to skills file (default: {DEFAULT_SKILLS_FILE})",
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

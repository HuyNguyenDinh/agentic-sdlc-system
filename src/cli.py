#!/usr/bin/env python3
"""IaC CLI for agentic SDLC workflows — like kubectl for your SDLC pipelines."""

import argparse
import sys
from pathlib import Path

import yaml

from src.schema import validate, EXAMPLE_WORKFLOW
from src.render import render_file

SCRIPTS_DIR = Path(__file__).resolve().parent


def cmd_create(args):
    path = Path(args.name)
    if not path.suffix:
        path = path.with_suffix(".yaml")

    if path.exists():
        print(f"Error: {path} already exists. Use --force to overwrite.")
        sys.exit(1)

    content = yaml.dump(EXAMPLE_WORKFLOW, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Customize name
    base = Path(args.name).stem
    content = content.replace("name: example-workflow", f"name: {base}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Created: {path}")


def cmd_validate(args):
    path = Path(args.yaml)
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    with open(path) as f:
        data = yaml.safe_load(f)

    errors = validate(data)
    if errors:
        print(f"Validation failed for {path}:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"✓ {path} is valid")


def cmd_apply(args):
    path = Path(args.yaml)
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    with open(path) as f:
        data = yaml.safe_load(f)

    errors = validate(data)
    if errors:
        print(f"Validation failed — cannot apply:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    output = args.output
    if not output:
        output = path.with_suffix(".md")

    render_file(str(path), str(output))
    print(f"Applied: {path} → {output}")


def main():
    parser = argparse.ArgumentParser(
        description="agentic-sdlc — IaC CLI for SDLC workflows"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="scaffold a new workflow YAML")
    p_create.add_argument("name", help="workflow name (e.g. my-workflow)")
    p_create.set_defaults(func=cmd_create)

    # validate
    p_validate = sub.add_parser("validate", help="validate a workflow YAML against schema")
    p_validate.add_argument("yaml", help="path to workflow YAML")
    p_validate.set_defaults(func=cmd_validate)

    # apply
    p_apply = sub.add_parser("apply", help="validate + render workflow YAML to markdown")
    p_apply.add_argument("yaml", help="path to workflow YAML")
    p_apply.add_argument("-o", "--output", help="output markdown path (default: same name, .md)")
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

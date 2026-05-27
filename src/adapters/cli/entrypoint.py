import argparse
import sys
from pathlib import Path
import yaml

from src.core.services.agent_service import AgentService
from src.adapters.fs_agent_repository import FSAgentRepository
from src.adapters.multica_adapter import MulticaAdapter
from src.core.services.workflow_service import validate, EXAMPLE_WORKFLOW
from src.adapters.markdown_renderer import render_file

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

def cmd_sync_agents(args):
    # Determine agents directory relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    agents_dir = project_root / "agents"
    
    repo = FSAgentRepository(base_path=agents_dir)
    pub = MulticaAdapter()
    service = AgentService(agent_repo=repo, agent_publisher=pub)
    
    success, failed = service.sync_all_agents()
    if failed > 0:
        sys.exit(1)
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="agentic-sdlc — Hexagonal IaC CLI for SDLC workflows"
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

    # sync-agents
    p_sync = sub.add_parser("sync-agents", help="scan agents directory recursively and publish to Multica")
    p_sync.set_defaults(func=cmd_sync_agents)

    args = parser.parse_args()
    args.func(args)

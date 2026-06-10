import argparse
import sys
from pathlib import Path
import yaml

from src.core.services.agent_service import AgentService
from src.adapters.fs_agent_repository import FSAgentRepository
from src.adapters.multica_adapter import MulticaAdapter
from src.core.services.workflow_service import validate, EXAMPLE_WORKFLOW
from src.adapters.markdown_renderer import render_file
from src.core.services.workflow_sync_service import WorkflowSyncService
from src.install_skills import install_skills_from_file, DEFAULT_SKILLS_FILE
from src.bootstrap_obsidian_wiki import DEFAULT_VAULT_PATH, run_bootstrap, run_post_bootstrap_check
from src.bootstrap_gitnexus import install_gitnexus, run_bootstrap as run_bootstrap_gitnexus
from src.bootstrap_multica_skills import sync_skills_to_multica, assign_skills_to_all_agents


DEFAULT_WORKFLOW = "workflow/orchestrator-debate.yaml"

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

def cmd_sync_agent(args):
    try:
        run_sync_agent(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


def run_sync_agent(args):
    if getattr(args, "dry_run", False):
        print(
            f"[dry-run] sync-agent --adapter {args.adapter}"
            + (f" --runtime-id {args.runtime_id}" if getattr(args, "runtime_id", None) else "")
        )
        return True

    # Determine agents directory relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    agents_dir = project_root / "agents"
    
    repo = FSAgentRepository(base_path=agents_dir)
    
    if args.adapter == "multica":
        pub = MulticaAdapter(runtime_id=getattr(args, "runtime_id", None))
    else:
        print(f"Error: Unknown adapter '{args.adapter}'", file=sys.stderr)
        sys.exit(1)
        
    service = AgentService(agent_repo=repo, agent_publisher=pub)
    
    success, failed = service.sync_all_agents()
    if failed > 0:
        raise RuntimeError(f"{failed} agent(s) failed to sync")
    return success

def cmd_sync_workflow(args):
    try:
        run_sync_workflow(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


def run_sync_workflow(args):
    workflow_value = getattr(args, "workflow", None) or getattr(args, "yaml", None)
    path = Path(workflow_value)
    if not path.exists():
        raise RuntimeError(f"{path} not found")

    if getattr(args, "dry_run", False):
        print(
            f"[dry-run] sync-workflow {path} --adapter {args.adapter}"
            + (f" --runtime-id {args.runtime_id}" if getattr(args, "runtime_id", None) else "")
        )
        return True

    if args.adapter == "multica":
        pub = MulticaAdapter(runtime_id=getattr(args, "runtime_id", None))
    else:
        raise RuntimeError(f"Unknown adapter '{args.adapter}'")

    service = WorkflowSyncService(publisher=pub)
    success = service.sync_workflow(str(path))
    if not success:
        raise RuntimeError(f"Failed to sync workflow {path}")
    return success


def cmd_bootstrap_wiki(args):
    try:
        run_bootstrap(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


def cmd_check_bootstrap(args):
    try:
        run_post_bootstrap_check(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

def cmd_bootstrap_gitnexus(args):
    try:
        run_bootstrap_gitnexus(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


def cmd_bootstrap_skills(args):
    try:
        run_bootstrap_skills(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


def run_bootstrap_skills(args):
    skill_ids = sync_skills_to_multica(dry_run=args.dry_run)
    if not skill_ids:
        if not args.dry_run:
            print("No skills to assign. Check that local skills exist and are importable.")
            return
        return
    assign_skills_to_all_agents(skill_ids, dry_run=args.dry_run)


def cmd_bootstrap(args):
    try:
        run_bootstrap(args)
        install_skills_from_file(Path(args.skills_file), dry_run=args.dry_run)
        install_gitnexus(dry_run=args.dry_run)
        run_sync_agent(args)
        run_sync_workflow(args)
        run_bootstrap_skills(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
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

    # sync-agent
    p_sync = sub.add_parser("sync-agent", help="scan agents directory recursively and publish to target adapter")
    p_sync.add_argument("--adapter", default="multica", choices=["multica"], help="target adapter to publish to (default: multica)")
    p_sync.add_argument("--runtime-id", help="runtime ID for the multica adapter")
    p_sync.set_defaults(func=cmd_sync_agent)

    # sync-workflow
    p_sync_wf = sub.add_parser("sync-workflow", help="validate, render, and sync a workflow YAML to target adapter as a squad")
    p_sync_wf.add_argument("yaml", help="path to workflow YAML")
    p_sync_wf.add_argument("--adapter", default="multica", choices=["multica"], help="target adapter to publish to (default: multica)")
    p_sync_wf.add_argument("--runtime-id", help="runtime ID for the target adapter")
    p_sync_wf.set_defaults(func=cmd_sync_workflow)

    # bootstrap
    p_bootstrap = sub.add_parser("bootstrap", help="bootstrap wiki, skills, GitNexus install, agents, and workflow sync")
    p_bootstrap.add_argument("--repo", help="private GitHub repository (owner/repo or URL)")
    p_bootstrap.add_argument("--branch", default="main", help="git branch to sync (default: main)")
    p_bootstrap.add_argument("--vault-path", default=DEFAULT_VAULT_PATH, help=f"vault path (default: {DEFAULT_VAULT_PATH})")
    p_bootstrap.add_argument("--non-interactive", action="store_true", help="fail instead of prompting when --repo is missing")
    p_bootstrap.add_argument("--force", action="store_true", help="allow unsafe operations where supported")
    p_bootstrap.add_argument("--dry-run", action="store_true", help="print actions without changing the system")
    p_bootstrap.add_argument("--skills-file", default=str(DEFAULT_SKILLS_FILE), help=f"skills file to install (default: {DEFAULT_SKILLS_FILE})")
    p_bootstrap.add_argument("--workflow", default=DEFAULT_WORKFLOW, help=f"workflow YAML to sync (default: {DEFAULT_WORKFLOW})")
    p_bootstrap.add_argument("--adapter", default="multica", choices=["multica"], help="target adapter to publish to (default: multica)")
    p_bootstrap.add_argument("--runtime-id", help="runtime ID for the multica adapter")
    p_bootstrap.set_defaults(func=cmd_bootstrap)

    # bootstrap-wiki
    p_bootstrap_wiki = sub.add_parser("bootstrap-wiki", help="bootstrap obsidian-wiki runtime and cron sync")
    p_bootstrap_wiki.add_argument("--repo", help="private GitHub repository (owner/repo or URL)")
    p_bootstrap_wiki.add_argument("--branch", default="main", help="git branch to sync (default: main)")
    p_bootstrap_wiki.add_argument("--vault-path", default=DEFAULT_VAULT_PATH, help=f"vault path (default: {DEFAULT_VAULT_PATH})")
    p_bootstrap_wiki.add_argument("--non-interactive", action="store_true", help="fail instead of prompting when --repo is missing")
    p_bootstrap_wiki.add_argument("--force", action="store_true", help="allow unsafe operations where supported")
    p_bootstrap_wiki.add_argument("--dry-run", action="store_true", help="print actions without changing the system")
    p_bootstrap_wiki.set_defaults(func=cmd_bootstrap_wiki)

    # check-wiki-bootstrap
    p_check = sub.add_parser("check-wiki-bootstrap", help="verify obsidian-wiki cron, env var, and git remote setup")
    p_check.add_argument("--repo", help="expected private GitHub repository (owner/repo or URL)")
    p_check.add_argument("--branch", default="main", help="git branch in cron sync (default: main)")
    p_check.add_argument("--vault-path", default=DEFAULT_VAULT_PATH, help=f"vault path (default: {DEFAULT_VAULT_PATH})")
    p_check.set_defaults(func=cmd_check_bootstrap)

    # bootstrap-gitnexus
    p_bootstrap_gitnexus = sub.add_parser("bootstrap-gitnexus", help="bootstrap GitNexus runtime and analysis flow")
    p_bootstrap_gitnexus.add_argument("--mode", choices=["monorepo", "multi-repo"], required=True, help="working mode")
    p_bootstrap_gitnexus.add_argument("--repo", help="monorepo input (owner/repo or URL)")
    p_bootstrap_gitnexus.add_argument("--repos", nargs="*", help="multi-repo inputs (owner/repo or URL)")
    p_bootstrap_gitnexus.add_argument("--group-name", help="GitNexus group name for multi-repo mode")
    p_bootstrap_gitnexus.add_argument("--dry-run", action="store_true", help="print actions without executing them")
    p_bootstrap_gitnexus.set_defaults(func=cmd_bootstrap_gitnexus)

    # bootstrap-skills
    p_bootstrap_skills = sub.add_parser("bootstrap-skills", help="import local skills into Multica workspace and assign to all agents")
    p_bootstrap_skills.add_argument("--dry-run", "-n", action="store_true", help="print actions without executing")
    p_bootstrap_skills.set_defaults(func=cmd_bootstrap_skills)

    args = parser.parse_args()
    args.func(args)


import yaml
from pathlib import Path
from src.core.ports.workflow_publisher import WorkflowPublisherPort
from src.core.domain.models import Workflow
from src.core.services.workflow_service import validate
from src.adapters.markdown_renderer import render_markdown

class WorkflowSyncService:
    def __init__(self, publisher: WorkflowPublisherPort):
        self.publisher = publisher

    def sync_workflow(self, yaml_path: str) -> bool:
        try:
            with open(yaml_path, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading workflow YAML file: {e}")
            return False

        if data is None or not isinstance(data, dict):
            print(f"Error: Workflow YAML at {yaml_path} is empty or invalid.")
            return False

        # Validate
        errors = validate(data)
        if errors:
            print(f"Validation failed for {yaml_path}:")
            for e in errors:
                print(f"  ✗ {e}")
            return False

        # Render markdown instructions using base filename as canonical relative path
        rel_path = Path(yaml_path).name
        rendered_md = render_markdown(data, yaml_rel=rel_path)

        # Construct Workflow domain model
        wf_data = data.get("workflow", {})
        wf_id = wf_data.get("name")
        wf_description = wf_data.get("description")
        wf_squad_leader = wf_data.get("squad_leader")

        # Collect all agent IDs defined in the YAML (preserving order)
        agents_list = data.get("agents", [])
        wf_agent_ids = [a["id"] for a in agents_list if "id" in a]

        workflow = Workflow(
            id=wf_id,
            instructions=rendered_md,
            squad_leader=wf_squad_leader,
            description=wf_description,
            agent_ids=wf_agent_ids
        )

        # Publish
        return self.publisher.publish(workflow)

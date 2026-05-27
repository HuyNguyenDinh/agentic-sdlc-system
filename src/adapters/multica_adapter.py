import subprocess
import sys
from typing import Union
from src.core.domain.models import Agent, Workflow
from src.core.ports.agent_publisher import AgentPublisherPort
from src.core.ports.workflow_publisher import WorkflowPublisherPort

class MulticaAdapter(AgentPublisherPort, WorkflowPublisherPort):
    def __init__(self, runtime_id: str = None):
        self.runtime_id = runtime_id

    def _run_cmd(self, args: list[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False
            )
        except FileNotFoundError:
            # Handle cases where multica CLI is not found on PATH
            res = subprocess.CompletedProcess(args=args, returncode=127)
            res.stderr = "multica: command not found"
            return res

    def publish(self, entity: Union[Agent, Workflow] = None, *, agent: Agent = None, workflow: Workflow = None) -> bool:
        target = entity or agent or workflow
        if target is None:
            raise ValueError("Must provide an entity, agent, or workflow to publish")

        if isinstance(target, Agent):
            return self._publish_agent(target)
        elif isinstance(target, Workflow):
            return self._publish_workflow(target)
        else:
            raise TypeError(f"Unsupported entity type for publishing: {type(target)}")

    def _publish_agent(self, agent: Agent) -> bool:
        print(f"Syncing agent {agent.id}...")
        
        # Check if agent exists in multica
        check_res = self._run_cmd(["multica", "agent", "get", agent.id])
        
        if check_res.returncode == 0:
            # Agent exists, perform update
            print(f"  Agent '{agent.id}' exists. Updating...")
            cmd = [
                "multica", "agent", "update", agent.id,
                "--instructions", agent.instructions
            ]
            if agent.description:
                cmd += ["--description", agent.description]
        else:
            # Agent does not exist, perform create
            print(f"  Agent '{agent.id}' not found. Creating...")
            cmd = [
                "multica", "agent", "create",
                "--name", agent.id,
                "--instructions", agent.instructions
            ]
            if self.runtime_id:
                cmd += ["--runtime-id", self.runtime_id]
            if agent.description:
                cmd += ["--description", agent.description]
                
        res = self._run_cmd(cmd)
        if res.returncode != 0:
            err_msg = res.stderr.strip() if res.stderr else "Unknown error"
            print(f"  ✗ Failed to sync '{agent.id}': {err_msg}", file=sys.stderr)
            return False
        else:
            print(f"  ✓ Successfully synced '{agent.id}'")
            return True

    def _publish_workflow(self, workflow: Workflow) -> bool:
        print(f"Syncing workflow {workflow.id}...")
        
        # Check if squad exists in multica
        check_res = self._run_cmd(["multica", "squad", "get", workflow.id])
        
        if check_res.returncode == 0:
            # Squad exists, perform update
            print(f"  Squad '{workflow.id}' exists. Updating...")
            cmd = [
                "multica", "squad", "update", workflow.id,
                "--instructions", workflow.instructions
            ]
            if workflow.description:
                cmd += ["--description", workflow.description]
        else:
            # Squad does not exist, perform create
            print(f"  Squad '{workflow.id}' not found. Creating...")
            cmd = [
                "multica", "squad", "create",
                "--name", workflow.id,
                "--instructions", workflow.instructions
            ]
            if workflow.description:
                cmd += ["--description", workflow.description]
                
        res = self._run_cmd(cmd)
        if res.returncode != 0:
            err_msg = res.stderr.strip() if res.stderr else "Unknown error"
            print(f"  ✗ Failed to sync '{workflow.id}': {err_msg}", file=sys.stderr)
            return False
        else:
            print(f"  ✓ Successfully synced '{workflow.id}'")
            return True

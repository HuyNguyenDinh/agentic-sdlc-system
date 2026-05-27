import json
import re
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

    def _resolve_agent_uuid(self, agent_slug: str) -> tuple[bool, str, str]:
        """Resolve agent slug to UUID via 'multica agent get'.
        Returns (found: bool, uuid: str, current_instructions: str).
        """
        get_res = self._run_cmd(["multica", "agent", "get", agent_slug])
        if get_res.returncode != 0:
            return False, agent_slug, ""
        try:
            data = json.loads(get_res.stdout)
            if isinstance(data, dict):
                return True, data.get("id", agent_slug), data.get("instructions", "") or ""
        except Exception:
            pass
        return True, agent_slug, ""

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
        
        # Resolve agent existence and UUID in one call
        found, actual_id, _ = self._resolve_agent_uuid(agent.id)
        
        if found:
            # Agent exists, perform update using the resolved UUID
            print(f"  Agent '{agent.id}' exists. Updating...")
            cmd = [
                "multica", "agent", "update", actual_id,
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
            ]
            if workflow.description:
                cmd += ["--description", workflow.description]
        else:
            # Squad does not exist, perform create
            print(f"  Squad '{workflow.id}' not found. Creating...")
            cmd = [
                "multica", "squad", "create",
                "--name", workflow.id,
                "--leader", workflow.squad_leader,
            ]
            if workflow.description:
                cmd += ["--description", workflow.description]
                
        res = self._run_cmd(cmd)
        if res.returncode != 0:
            err_msg = res.stderr.strip() if res.stderr else "Unknown error"
            print(f"  ✗ Failed to sync squad '{workflow.id}': {err_msg}", file=sys.stderr)
            return False
        else:
            print(f"  ✓ Successfully synced squad '{workflow.id}'")

        # Append workflow instructions to the squad leader agent
        if workflow.squad_leader and workflow.instructions:
            print(f"  Updating squad leader '{workflow.squad_leader}' instructions...")
            
            # Fetch current instructions and actual ID for the squad leader agent
            found, actual_leader_id, current_instructions = self._resolve_agent_uuid(workflow.squad_leader)

            start_marker = f"<!-- WORKFLOW_START: {workflow.id} -->"
            end_marker = f"<!-- WORKFLOW_END: {workflow.id} -->"
            workflow_block = f"{start_marker}\n{workflow.instructions}\n{end_marker}"
            
            pattern = re.compile(rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
            
            if re.search(pattern, current_instructions):
                new_instructions = re.sub(pattern, workflow_block, current_instructions)
            else:
                if current_instructions:
                    new_instructions = current_instructions.rstrip() + "\n\n" + workflow_block
                else:
                    new_instructions = workflow_block

            leader_cmd = [
                "multica", "agent", "update", actual_leader_id,
                "--instructions", new_instructions,
            ]
            leader_res = self._run_cmd(leader_cmd)
            if leader_res.returncode != 0:
                err_msg = leader_res.stderr.strip() if leader_res.stderr else "Unknown error"
                print(f"  ✗ Failed to update squad leader '{workflow.squad_leader}': {err_msg}", file=sys.stderr)
                return False
            else:
                print(f"  ✓ Successfully updated squad leader '{workflow.squad_leader}' instructions")

        # Register all agents in the workflow as squad members
        if workflow.agent_ids:
            print(f"  Registering {len(workflow.agent_ids)} agent(s) as squad members...")
            for agent_slug in workflow.agent_ids:
                found, agent_uuid, _ = self._resolve_agent_uuid(agent_slug)
                if not found:
                    print(f"    ⚠ Agent '{agent_slug}' not found in Multica — skipping member registration", file=sys.stderr)
                    continue

                member_cmd = [
                    "multica", "squad", "member", "add", workflow.id,
                    "--member-id", agent_uuid,
                    "--type", "agent",
                ]
                member_res = self._run_cmd(member_cmd)
                if member_res.returncode != 0:
                    err_msg = member_res.stderr.strip() if member_res.stderr else "Unknown error"
                    print(f"    ✗ Failed to add '{agent_slug}' as squad member: {err_msg}", file=sys.stderr)
                else:
                    print(f"    ✓ Added '{agent_slug}' as squad member")

        return True


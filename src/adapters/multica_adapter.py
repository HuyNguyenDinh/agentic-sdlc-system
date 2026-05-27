import subprocess
import sys
from src.core.domain.models import Agent
from src.core.ports.agent_publisher import AgentPublisherPort

class MulticaAdapter(AgentPublisherPort):
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

    def publish(self, agent: Agent) -> bool:
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
            if agent.description:
                cmd += ["--description", agent.description]
                
        res = self._run_cmd(cmd)
        if res.returncode != 0:
            print(f"  ✗ Failed to sync '{agent.id}': {res.stderr.strip()}", file=sys.stderr)
            return False
        else:
            print(f"  ✓ Successfully synced '{agent.id}'")
            return True

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError, root_validator


class AgentIacEnvironment(BaseModel):
    name: str
    variables: Dict[str, str] = Field(default_factory=dict)
    secrets: List[str] = Field(default_factory=list)


class AgentIacResource(BaseModel):
    type: str
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentIacPermissions(BaseModel):
    allowed_tools: List[str] = Field(default_factory=list)
    read_access: List[str] = Field(default_factory=list)
    write_access: List[str] = Field(default_factory=list)


class AgentIacSpec(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    environment: AgentIacEnvironment
    resources: List[AgentIacResource] = Field(default_factory=list)
    permissions: AgentIacPermissions
    entrypoint: str
    timeout_seconds: int = Field(gt=0, default=3600)
    max_concurrent_runs: int = Field(gt=0, default=1)

    @root_validator
    def check_entrypoint_exists(cls, values):
        entrypoint = values.get('entrypoint')
        if not entrypoint:
            raise ValueError("entrypoint must not be empty")
        return values


AGENT_IAC_SCHEMA = AgentIacSpec.schema()


def validate_agent_iac(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate agent IaC definition against schema. Returns validated data on success."""
    try:
        instance = AgentIacSpec(**data)
        return instance.dict()
    except ValidationError as e:
        raise ValueError(f"Agent IaC validation failed: {e}") from e

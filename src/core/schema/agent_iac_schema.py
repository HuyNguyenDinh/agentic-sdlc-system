"""
Standalone Agent IaC Schema for instruction rendering.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError, conlist, confloat, conint


ID_PATTERN = r"^[a-z][a-z0-9-]*$"


class RuntimeConfig(BaseModel):
    model: str = "claude-3-7-sonnet"
    temperature: confloat(ge=0, le=2) = 0.2
    max_tokens: conint(ge=1) = 4096
    cache_enabled: bool = True
    max_turns: conint(ge=1) = 3


class KnowledgeBinding(BaseModel):
    source: str = Field(pattern=ID_PATTERN)
    mode: str = Field(default="implicit", enum=["prefetch", "on_demand", "implicit"])
    injection: str = Field(default="header", enum=["header", "footer", "inline"])
    scope: List[str] = Field(default_factory=list)
    access: List[str] = Field(default=["read"], min_length=1)


class KnowledgePolicy(BaseModel):
    on_complete: str = Field(default="none", enum=["none", "push", "sync"])
    target: Optional[str] = Field(pattern=ID_PATTERN, default=None)
    format: str = Field(default="markdown", enum=["markdown", "structured", "raw"])


class KnowledgeConfig(BaseModel):
    bindings: List[KnowledgeBinding] = Field(default_factory=list)
    update_policy: KnowledgePolicy = Field(default_factory=KnowledgePolicy)


class InstructionVariable(BaseModel):
    name: str
    type: str = Field(default="string", enum=["string", "integer", "boolean"])
    required: bool = False
    default: Optional[Any] = None


class InstructionsConfig(BaseModel):
    variables: List[InstructionVariable] = Field(default_factory=list)
    inject_sections: List[str] = Field(default_factory=lambda: ["knowledge_bindings", "runtime_config"])
    render_order: List[str] = Field(default_factory=lambda: ["header_knowledge", "base_instructions", "runtime_parameters"])


class AgentIacSpec(BaseModel):
    version: conint(ge=1)
    agent: 'AgentSpec'


class AgentSpec(BaseModel):
    id: str = Field(pattern=ID_PATTERN)
    role: str
    path: str
    description: Optional[str] = None
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    instructions: InstructionsConfig = Field(default_factory=InstructionsConfig)
    skills: List[str] = Field(default_factory=list)


AgentIacSpec.update_forward_refs()

AGENT_IAC_SCHEMA = AgentIacSpec.model_json_schema()


def validate_agent_iac(data: Dict[str, Any]) -> List[str]:
    """Validate Agent IaC definition against schema. Return list of errors, empty if valid."""
    try:
        AgentIacSpec(**data)
        return []
    except ValidationError as e:
        return [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]

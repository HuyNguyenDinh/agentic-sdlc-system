import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


STEP_TYPES = ["delegate", "debate", "hitl", "fanout"]

ID_PATTERN = r"^[a-z][a-z0-9-]*$"

JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://agentic-sdlc/workflow-schema",
    "title": "Agentic SDLC Workflow",
    "type": "object",
    "required": ["workflow", "agents", "steps"],
    "properties": {
        "workflow": {
            "type": "object",
            "required": ["name", "squad_leader"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "max_turn": {"type": "integer", "minimum": 1, "default": 3},
                "squad_leader": {"type": "string"},
            },
        },
        "agents": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "role"],
                "properties": {
                    "id": {"type": "string", "pattern": ID_PATTERN},
                    "role": {"type": "string"},
                    "path": {"type": "string"},
                },
            },
        },
        "knowledge_sources": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "description", "access"],
                "properties": {
                    "id": {"type": "string", "pattern": ID_PATTERN},
                    "type": {"enum": ["wiki", "repository", "external"]},
                    "description": {"type": "string"},
                    "access": {
                        "type": "array",
                        "items": {"enum": ["read", "write"]},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
            },
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "type", "description"],
                "properties": {
                    "id": {"type": "string", "pattern": ID_PATTERN},
                    "type": {"enum": STEP_TYPES},
                    "description": {"type": "string"},
                    "input": {"type": "string"},
                    "output": {"type": "string"},
                    "actor": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ]
                    },
                    "critic": {"type": "string"},
                    "artifact": {"type": "string"},
                    "max_turn": {"type": "integer", "minimum": 1},
                    "on_approved": {"type": "string"},
                    "on_rejected": {"type": "string"},
                    "on_max_turn_reached": {"type": "string"},
                    "debates": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["actor", "critic", "artifact"],
                            "properties": {
                                "actor": {"type": "string"},
                                "critic": {"type": "string"},
                                "artifact": {"type": "string"},
                                "max_turn": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                    "workers": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["id", "actor", "output"],
                            "properties": {
                                "id": {"type": "string"},
                                "actor": {"type": "string"},
                                "output": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    },
}


def validate(data: dict) -> list[str]:
    errors: list[str] = []

    wf = data.get("workflow", {})
    if not isinstance(wf, dict):
        errors.append("top-level 'workflow' must be an object")
    else:
        if not wf.get("name"):
            errors.append("workflow.name is required")
        if not wf.get("squad_leader"):
            errors.append("workflow.squad_leader is required")

    agents = data.get("agents", [])
    if not isinstance(agents, list) or not agents:
        errors.append("agents must be a non-empty array")
    else:
        agent_ids = set()
        for i, a in enumerate(agents):
            aid = a.get("id", "")
            if not aid:
                errors.append(f"agents[{i}].id is required")
            elif aid in agent_ids:
                errors.append(f"agents[{i}].id '{aid}' is duplicated")
            else:
                agent_ids.add(aid)
            if not a.get("role"):
                errors.append(f"agents[{i}].role is required")

    steps = data.get("steps", [])
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty array")
    else:
        step_ids = set()
        for i, step in enumerate(steps):
            sid = step.get("id", "")
            if not sid:
                errors.append(f"steps[{i}].id is required")
            elif sid in step_ids:
                errors.append(f"steps[{i}].id '{sid}' is duplicated")
            else:
                step_ids.add(sid)

            stype = step.get("type", "")
            if stype not in STEP_TYPES:
                errors.append(f"steps[{i}].type must be one of {STEP_TYPES}, got '{stype}'")

            if not step.get("description"):
                errors.append(f"steps[{i}].description is required")

            if stype == "delegate":
                if not step.get("actor"):
                    errors.append(f"steps[{i}] delegate step requires 'actor'")

            elif stype == "debate":
                if "debates" in step:
                    for j, d in enumerate(step["debates"]):
                        if not d.get("actor"):
                            errors.append(f"steps[{i}].debates[{j}].actor is required")
                        if not d.get("critic"):
                            errors.append(f"steps[{i}].debates[{j}].critic is required")
                else:
                    if not step.get("actor"):
                        errors.append(f"steps[{i}] debate step requires 'actor'")
                    if not step.get("critic"):
                        errors.append(f"steps[{i}] debate step requires 'critic'")

            elif stype == "hitl":
                if not step.get("on_approved"):
                    errors.append(f"steps[{i}] hitl step requires 'on_approved'")
                if not step.get("on_rejected"):
                    errors.append(f"steps[{i}] hitl step requires 'on_rejected'")

            elif stype == "fanout":
                if not step.get("workers"):
                    errors.append(f"steps[{i}] fanout step requires 'workers'")
                else:
                    for j, w in enumerate(step["workers"]):
                        if not w.get("id"):
                            errors.append(f"steps[{i}].workers[{j}].id is required")
                        if not w.get("actor"):
                            errors.append(f"steps[{i}].workers[{j}].actor is required")

    # Validate knowledge_sources if present
    ks = data.get("knowledge_sources")
    if ks is not None:
        if not isinstance(ks, list):
            errors.append("knowledge_sources must be an array")
        else:
            ks_ids = set()
            import re
            id_re = re.compile(ID_PATTERN)
            for i, source in enumerate(ks):
                if not isinstance(source, dict):
                    errors.append(f"knowledge_sources[{i}] must be an object")
                    continue

                for fld in ["id", "type", "description", "access"]:
                    if fld not in source:
                        errors.append(f"knowledge_sources[{i}].{fld} is required")

                sid = source.get("id")
                if sid:
                    if not isinstance(sid, str):
                        errors.append(f"knowledge_sources[{i}].id must be a string")
                    elif not id_re.match(sid):
                        errors.append(f"knowledge_sources[{i}].id '{sid}' must match pattern {ID_PATTERN}")
                    elif sid in ks_ids:
                        errors.append(f"knowledge_sources[{i}].id '{sid}' is duplicated")
                    else:
                        ks_ids.add(sid)

                stype = source.get("type")
                if stype and stype not in ["wiki", "repository", "external"]:
                    errors.append(f"knowledge_sources[{i}].type must be one of ['wiki', 'repository', 'external'], got '{stype}'")

                sdesc = source.get("description")
                if sdesc and not isinstance(sdesc, str):
                    errors.append(f"knowledge_sources[{i}].description must be a string")

                access = source.get("access")
                if access is not None:
                    if not isinstance(access, list) or not access:
                        errors.append(f"knowledge_sources[{i}].access must be a non-empty array")
                    else:
                        for a in access:
                            if a not in ["read", "write"]:
                                errors.append(f"knowledge_sources[{i}].access item must be one of ['read', 'write'], got '{a}'")

    return errors


def write_schema(path: str) -> None:
    with open(path, "w") as f:
        json.dump(JSON_SCHEMA, f, indent=2)
        f.write("\n")


EXAMPLE_WORKFLOW = {
    "workflow": {
        "name": "example-workflow",
        "description": "An example multi-agent SDLC workflow.",
        "max_turn": 3,
        "squad_leader": "pm-agent",
    },
    "agents": [
        {"id": "pm-agent", "role": "Squad Leader", "path": "agents/management/pm-agent.md"},
        {"id": "dev-agent", "role": "Developer", "path": "agents/coding/coder.md"},
        {"id": "reviewer-agent", "role": "Reviewer", "path": "agents/coding/code-critic.md"},
    ],
    "steps": [
        {
            "id": "design",
            "type": "delegate",
            "description": "Architect designs the solution",
            "actor": "dev-agent",
            "output": "design-doc",
        },
        {
            "id": "review",
            "type": "debate",
            "description": "Review the design",
            "actor": "dev-agent",
            "critic": "reviewer-agent",
            "artifact": "design-doc",
            "max_turn": 2,
            "on_approved": "implement",
        },
        {
            "id": "implement",
            "type": "delegate",
            "description": "Implement the solution",
            "actor": "dev-agent",
            "input": "design-doc",
        },
    ],
}

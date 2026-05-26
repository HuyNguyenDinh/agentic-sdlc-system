import sys
from src.schema import validate

def run_tests():
    print("Running schema validation tests...")

    # 1. Base workflow that is valid
    valid_wf = {
        "workflow": {
            "name": "test-workflow",
            "description": "A workflow description",
            "squad_leader": "lead-agent"
        },
        "agents": [
            {"id": "lead-agent", "role": "Lead", "path": "agents/lead.md"}
        ],
        "steps": [
            {
                "id": "step1",
                "type": "delegate",
                "description": "First step",
                "actor": "lead-agent"
            }
        ]
    }

    # Verify base passes
    assert len(validate(valid_wf)) == 0, f"Base workflow failed: {validate(valid_wf)}"

    # 2. Add valid knowledge_sources
    valid_wf["knowledge_sources"] = [
        {
            "id": "llm-wiki",
            "type": "wiki",
            "description": "Knowledge Base",
            "access": ["read", "write"]
        },
        {
            "id": "codebase",
            "type": "repository",
            "description": "Codebase",
            "access": ["read"]
        }
    ]
    assert len(validate(valid_wf)) == 0, f"Valid knowledge_sources failed: {validate(valid_wf)}"

    # 3. Invalid: Non-list knowledge_sources
    bad_wf1 = valid_wf.copy()
    bad_wf1["knowledge_sources"] = "not a list"
    errs = validate(bad_wf1)
    assert any("knowledge_sources must be an array" in e for e in errs), f"Expected list error, got {errs}"

    # 4. Invalid: Missing required fields
    bad_wf2 = {
        "workflow": valid_wf["workflow"],
        "agents": valid_wf["agents"],
        "steps": valid_wf["steps"],
        "knowledge_sources": [
            {
                "id": "incomplete-source",
                # missing type, description, access
            }
        ]
    }
    errs = validate(bad_wf2)
    assert any("type is required" in e for e in errs), f"Expected missing type error, got {errs}"
    assert any("description is required" in e for e in errs), f"Expected missing desc error, got {errs}"
    assert any("access is required" in e for e in errs), f"Expected missing access error, got {errs}"

    # 5. Invalid: Duplicate IDs
    bad_wf3 = {
        "workflow": valid_wf["workflow"],
        "agents": valid_wf["agents"],
        "steps": valid_wf["steps"],
        "knowledge_sources": [
            {"id": "wiki-1", "type": "wiki", "description": "D1", "access": ["read"]},
            {"id": "wiki-1", "type": "wiki", "description": "D2", "access": ["write"]}
        ]
    }
    errs = validate(bad_wf3)
    assert any("id 'wiki-1' is duplicated" in e for e in errs), f"Expected duplicate error, got {errs}"

    # 6. Invalid: Invalid ID Pattern
    bad_wf4 = {
        "workflow": valid_wf["workflow"],
        "agents": valid_wf["agents"],
        "steps": valid_wf["steps"],
        "knowledge_sources": [
            {"id": "Wiki_Invalid!", "type": "wiki", "description": "D1", "access": ["read"]}
        ]
    }
    errs = validate(bad_wf4)
    assert any("must match pattern" in e for e in errs), f"Expected pattern error, got {errs}"

    # 7. Invalid: Wrong Enum Type
    bad_wf5 = {
        "workflow": valid_wf["workflow"],
        "agents": valid_wf["agents"],
        "steps": valid_wf["steps"],
        "knowledge_sources": [
            {"id": "wiki-1", "type": "blog", "description": "D1", "access": ["read"]}
        ]
    }
    errs = validate(bad_wf5)
    assert any("type must be one of" in e for e in errs), f"Expected enum error, got {errs}"

    # 8. Invalid: Empty Access
    bad_wf6 = {
        "workflow": valid_wf["workflow"],
        "agents": valid_wf["agents"],
        "steps": valid_wf["steps"],
        "knowledge_sources": [
            {"id": "wiki-1", "type": "wiki", "description": "D1", "access": []}
        ]
    }
    errs = validate(bad_wf6)
    assert any("access must be a non-empty array" in e for e in errs), f"Expected empty access error, got {errs}"

    print("✓ All validation tests pass successfully!")

if __name__ == "__main__":
    run_tests()

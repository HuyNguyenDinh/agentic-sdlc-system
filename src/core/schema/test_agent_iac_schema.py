import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.core.schema.agent_iac_schema import validate_agent_iac, AGENT_IAC_SCHEMA


def test_agent_iac_schema_exists():
    assert AGENT_IAC_SCHEMA is not None
    assert "properties" in AGENT_IAC_SCHEMA
    assert "agent" in AGENT_IAC_SCHEMA["properties"]
    assert "version" in AGENT_IAC_SCHEMA["properties"]


def test_valid_agent_iac_passes_validation():
    valid_data = {
        "version": 1,
        "agent": {
            "id": "test-agent",
            "role": "Engineer",
            "path": "agents/test/test-agent.md",
            "description": "Test agent",
        }
    }

    errors = validate_agent_iac(valid_data)
    assert errors == []


def test_missing_required_fields_fails():
    invalid_data = {
        "version": 1,
        # missing "agent" key entirely
    }

    errors = validate_agent_iac(invalid_data)
    assert len(errors) > 0
    assert any("agent" in e for e in errors)


def test_empty_agent_id_fails():
    invalid_data = {
        "version": 1,
        "agent": {
            "id": "",  # fails pattern ^[a-z][a-z0-9-]*$
            "role": "Engineer",
            "path": "agents/test/test-agent.md",
        }
    }

    errors = validate_agent_iac(invalid_data)
    assert len(errors) > 0


def test_negative_temperature_fails():
    invalid_data = {
        "version": 1,
        "agent": {
            "id": "test-agent",
            "role": "Engineer",
            "path": "agents/test/test-agent.md",
            "runtime": {"temperature": -1.0},
        }
    }

    errors = validate_agent_iac(invalid_data)
    assert len(errors) > 0

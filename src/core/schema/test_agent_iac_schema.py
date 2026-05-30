import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.core.schema.agent_iac_schema import validate_agent_iac, AGENT_IAC_SCHEMA


def test_agent_iac_schema_exists():
    assert AGENT_IAC_SCHEMA is not None
    assert "properties" in AGENT_IAC_SCHEMA
    assert "name" in AGENT_IAC_SCHEMA["properties"]
    assert "version" in AGENT_IAC_SCHEMA["properties"]


def test_valid_agent_iac_passes_validation():
    valid_data = {
        "name": "test-agent",
        "version": "1.0.0",
        "description": "Test agent",
        "environment": {
            "name": "production",
            "variables": {"LOG_LEVEL": "INFO"},
            "secrets": ["API_KEY"]
        },
        "resources": [
            {"type": "database", "name": "test-db", "config": {"engine": "postgres"}}
        ],
        "permissions": {
            "allowed_tools": ["bash", "read_file"],
            "read_access": ["/tmp"],
            "write_access": ["/tmp/out"]
        },
        "entrypoint": "main.py",
        "timeout_seconds": 7200,
        "max_concurrent_runs": 2
    }

    result = validate_agent_iac(valid_data)
    assert result["name"] == "test-agent"
    assert result["timeout_seconds"] == 7200


def test_missing_required_fields_fails():
    invalid_data = {
        "version": "1.0.0",
        "environment": {"name": "prod"},
        "permissions": {},
        "entrypoint": "main.py"
    }

    with pytest.raises(ValueError) as excinfo:
        validate_agent_iac(invalid_data)
    assert "validation failed" in str(excinfo.value)


def test_empty_entrypoint_fails():
    invalid_data = {
        "name": "test-agent",
        "version": "1.0.0",
        "environment": {"name": "prod"},
        "permissions": {},
        "entrypoint": ""
    }

    with pytest.raises(ValueError):
        validate_agent_iac(invalid_data)


def test_negative_timeout_fails():
    invalid_data = {
        "name": "test-agent",
        "version": "1.0.0",
        "environment": {"name": "prod"},
        "permissions": {},
        "entrypoint": "main.py",
        "timeout_seconds": -10
    }

    with pytest.raises(ValueError):
        validate_agent_iac(invalid_data)

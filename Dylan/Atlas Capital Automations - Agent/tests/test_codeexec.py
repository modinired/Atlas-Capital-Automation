"""Tests for the CodeExec MCP in the agent edition.

These tests ensure that the code execution service exposed via the
agent edition's MCP API functions correctly.  They mirror the
coverage provided for the base edition to guarantee parity between
SKUs.
"""

import json

from fastapi.testclient import TestClient

from app.mcp_api import mcp_app


def test_execute_python_success() -> None:
    """Verify that a simple Python script executes successfully."""
    client = TestClient(mcp_app)
    payload = {
        "language": "python",
        "code": "print('agent')",
    }
    response = client.post("/mcp/codeexec/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["returncode"] == 0
    assert "agent" in data["stdout"]
    assert not data["timed_out"]


def test_execute_unsupported_language() -> None:
    """Unsupported languages should return an error return code."""
    client = TestClient(mcp_app)
    payload = {
        "language": "ruby",
        "code": "puts 'hi'",
    }
    response = client.post("/mcp/codeexec/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["returncode"] == -1
    assert "Unsupported language" in data["stderr"]


def test_execute_timeout() -> None:
    """Scripts that exceed the timeout should be terminated."""
    client = TestClient(mcp_app)
    payload = {
        "code": "while True: pass",
        "timeout": 1,
    }
    response = client.post("/mcp/codeexec/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["timed_out"] is True
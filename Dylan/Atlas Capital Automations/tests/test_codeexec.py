"""Tests for the CodeExec MCP.

These tests exercise the HTTP endpoints exposed by the MCP API to
ensure that the code execution service behaves as expected.  They
verify that Python code runs successfully, unsupported languages are
rejected and timeouts are honoured.
"""

import json

from fastapi.testclient import TestClient

from app.mcp_api import mcp_app


def test_execute_python_success() -> None:
    """Verify that a simple Python script executes successfully."""
    client = TestClient(mcp_app)
    payload = {
        "language": "python",
        "code": "print('hello')",
    }
    response = client.post("/mcp/codeexec/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["returncode"] == 0
    assert "hello" in data["stdout"]
    assert not data["timed_out"]


def test_execute_unsupported_language() -> None:
    """Unsupported languages should return an error return code."""
    client = TestClient(mcp_app)
    payload = {
        "language": "bash",
        "code": "echo hi",
    }
    response = client.post("/mcp/codeexec/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    # For unsupported languages returncode is -1 and stderr contains message
    assert data["returncode"] == -1
    assert "Unsupported language" in data["stderr"]


def test_execute_timeout() -> None:
    """Scripts that exceed the timeout should be terminated."""
    client = TestClient(mcp_app)
    # Infinite loop to trigger timeout
    payload = {
        "code": "while True: pass",
        "timeout": 1,
    }
    response = client.post("/mcp/codeexec/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["timed_out"] is True
    # When timed out, returncode may be -1 or whatever but we check timed_out flag
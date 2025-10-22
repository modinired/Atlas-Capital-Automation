#!/usr/bin/env python3
"""
Quick launch script for the Terry Delmonaco Presents: AI API and MCP server.

This script is intended to provide a double‑clickable entry point for end users
who prefer not to run commands manually.  It launches both the main risk
scoring API and the MCP server (Knowledge, Triangulator, Policy, CodeExec and
Workflow endpoints) using Uvicorn, waits for them to start, and opens the
interactive API documentation in the default web browser.

Environment variables:

* ``API_PORT`` (default 8000) – port for the risk scoring API.
* ``MCP_PORT`` (default 9000) – port for the MCP server.
* Any of the variables documented in the README (API_KEY, RATE_LIMIT_PER_MIN, etc.)
  may also be set before launching to configure authentication, rate limiting,
  tracing, etc.

Usage:

    python launch.py

The script blocks until interrupted (Ctrl+C).  On termination it will
terminate both servers.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import webbrowser


def run_uvicorn(app_path: str, port: int) -> subprocess.Popen:
    """Spawn a Uvicorn process for the given ASGI app on the specified port."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        app_path,
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    # Inherit the current environment so API_KEY and other variables propagate.
    return subprocess.Popen(cmd, env=os.environ.copy())


def main() -> None:
    # Determine ports from environment or defaults
    api_port = int(os.environ.get("API_PORT", "8000"))
    mcp_port = int(os.environ.get("MCP_PORT", "9000"))

    # Launch the risk scoring API and MCP server
    print(f"Starting risk API on port {api_port}...")
    risk_proc = run_uvicorn("app.main:app", api_port)
    print(f"Starting MCP server on port {mcp_port}...")
    mcp_proc = run_uvicorn("app.mcp_api:mcp_app", mcp_port)

    # Give servers a moment to start before opening the browser
    time.sleep(2)
    try:
        # Open the Swagger docs for the main API
        webbrowser.open(f"http://localhost:{api_port}/docs")
    except Exception:
        pass
    print("Servers started.  API docs available at:")
    print(f"  • Risk API: http://localhost:{api_port}/docs")
    print(f"  • MCP API:  http://localhost:{mcp_port}/docs")
    print("Press Ctrl+C to stop.")

    try:
        # Wait for both processes to exit (this blocks indefinitely)
        risk_proc.wait()
        mcp_proc.wait()
    except KeyboardInterrupt:
        print("\nTerminating servers...")
        risk_proc.terminate()
        mcp_proc.terminate()
        risk_proc.wait()
        mcp_proc.wait()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
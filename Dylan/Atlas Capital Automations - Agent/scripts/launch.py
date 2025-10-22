#!/usr/bin/env python3
"""
Quick launch script for the Terry Delmonaco Presents: AI Agent Edition.

This script provides a simple entry point for end users who want to start
the risk scoring API and the MCP server (including the orchestrator agent
and CLI tools) without typing Uvicorn commands.  It launches the two
FastAPI applications on configurable ports, waits briefly, and opens the
interactive API documentation pages in the default web browser.

Environment variables:

* ``API_PORT`` (default 8000) – port for the risk scoring API.
* ``MCP_PORT`` (default 9000) – port for the MCP server.
* ``API_KEY``, ``RATE_LIMIT_PER_MIN``, ``MODEL_PATH`` and other variables
  documented in the README are passed through to both processes.

Usage:

    python scripts/launch.py

The script blocks until interrupted (Ctrl+C).  On termination it will
terminate both servers.  It does not start the front‑end dashboard – run
``npm run dev`` in the ``dashboard`` directory separately if you wish to
use the web UI.
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
    return subprocess.Popen(cmd, env=os.environ.copy())


def main() -> None:
    api_port = int(os.environ.get("API_PORT", "8000"))
    mcp_port = int(os.environ.get("MCP_PORT", "9000"))

    print(f"Starting risk API on port {api_port}...")
    risk_proc = run_uvicorn("app.main:app", api_port)
    print(f"Starting MCP server on port {mcp_port}...")
    mcp_proc = run_uvicorn("app.mcp_api:mcp_app", mcp_port)

    # Wait a moment for the servers to come up
    time.sleep(2)
    try:
        webbrowser.open(f"http://localhost:{api_port}/docs")
    except Exception:
        pass
    print("Servers started. API docs available at:")
    print(f"  • Risk API: http://localhost:{api_port}/docs")
    print(f"  • MCP API:  http://localhost:{mcp_port}/docs")
    print("Press Ctrl+C to stop.")

    try:
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
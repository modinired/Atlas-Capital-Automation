#!/usr/bin/env bash
#
# Cross‑platform launcher for the Agent Edition (Linux).
#
# This script activates the project's virtual environment if present
# and runs the Python launcher in scripts/launch.py, which starts the
# risk API and MCP server.  Any command‑line arguments are passed
# through to the Python script.

set -euo pipefail
cd "$(dirname "$0")"
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi
exec python3 scripts/launch.py "$@"
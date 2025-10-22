#!/usr/bin/env bash
#
# Cross‑platform launcher for Terry Delmonaco Presents: AI (Linux).
#
# This script starts the risk scoring API and MCP server using the
# Python helper in scripts/launch.py.  It attempts to activate the
# project's virtual environment if one exists.  Any arguments passed
# to this script are forwarded to the Python launcher (e.g. you can
# override environment variables on the command line).

set -euo pipefail

# Change to the directory containing this script so relative paths work
cd "$(dirname "$0")"

# Activate virtual environment if present
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi

# Run the Python launcher
exec python3 scripts/launch.py "$@"
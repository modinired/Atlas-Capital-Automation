#!/usr/bin/env bash
#
# macOS double‑click launcher for Terry Delmonaco Presents: AI.
#
# This script mirrors launch.sh but uses the .command extension so
# Finder recognises it as an executable script.  It activates the
# virtual environment if present and starts both the API and MCP
# server via scripts/launch.py.

set -euo pipefail
cd "$(dirname "$0")"
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi
exec python3 scripts/launch.py "$@"
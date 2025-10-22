#!/usr/bin/env bash
#
# macOS launcher for the Agent Edition.
#
# Identical to launch.sh but with a .command extension so Finder
# treats it as an executable script.  Activates the virtual
# environment and starts the API and MCP via the Python launcher.

set -euo pipefail
cd "$(dirname "$0")"
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi
exec python3 scripts/launch.py "$@"
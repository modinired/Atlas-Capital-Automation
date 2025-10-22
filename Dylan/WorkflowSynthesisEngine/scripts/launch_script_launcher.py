
"""Launch Script Launcher Pro (GUI) with integrated CESAR workflow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

LAUNCHER_ROOT = Path(__file__).resolve().parent.parent / "external_launchers" / "script_launcher"


def main() -> None:
    entrypoint = LAUNCHER_ROOT / "main.py"
    if not entrypoint.exists():
        raise FileNotFoundError(f"Script Launcher entrypoint not found: {entrypoint}")
    subprocess.run([sys.executable, str(entrypoint), "gui"], cwd=str(LAUNCHER_ROOT), check=True)


if __name__ == "__main__":
    main()

"""Launches the Workflow Synthesis Engine GUI locally."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the Workflow Synthesis Engine GUI")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the browser")
    parser.add_argument("--uvicorn-extra", nargs=argparse.REMAINDER, help="Additional uvicorn args")
    args = parser.parse_args()

    app_path = "cesar_src.ui.app:app"
    uvicorn_cmd = [sys.executable, "-m", "uvicorn", app_path, "--host", args.host, "--port", str(args.port)]
    if args.uvicorn_extra:
        uvicorn_cmd.extend(args.uvicorn_extra)

    print("Launching Workflow Synthesis GUI...")
    print("Command:", " ".join(uvicorn_cmd))

    proc = subprocess.Popen(uvicorn_cmd)

    url = f"http://{args.host}:{args.port}/"
    time.sleep(1.0)
    if not args.no_browser:
        webbrowser.open(url)
        print(f"Browser opened at {url}")
    else:
        print(f"Visit {url}")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("Shutting down GUI...")
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()

"""Workflow Synthesis Engine entrypoint for Script Launcher Pro."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cesar_src.cli.extract import _run as run_workflow


async def _execute(config: Path, transcript: Path, endpoint: str | None) -> dict:
    return await run_workflow(config, transcript, endpoint)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the CESAR Workflow Synthesis Engine from Script Launcher Pro")
    parser.add_argument("--config", type=Path, required=True, help="Path to CESAR config.yaml")
    parser.add_argument("--transcript", type=Path, required=True, help="Path to transcript text file")
    parser.add_argument("--endpoint", type=str, default=None, help="LLM endpoint override")
    args = parser.parse_args()

    if not args.config.exists():
        raise FileNotFoundError(f"Config not found: {args.config}")
    if not args.transcript.exists():
        raise FileNotFoundError(f"Transcript not found: {args.transcript}")

    result = asyncio.run(_execute(args.config, args.transcript, args.endpoint))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

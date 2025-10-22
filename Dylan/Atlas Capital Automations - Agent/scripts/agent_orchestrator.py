#!/usr/bin/env python
"""
Agent Orchestrator CLI
----------------------

This script provides a simple command‑line interface for executing
Card workflows in the Multi‑Component Platform (MCP).  It can be
used to run high‑level processes, such as Quarterly Business Review
preparation or Incident Postmortem generation, without writing code.

Usage example:

    python scripts/agent_orchestrator.py --card QBR --inputs inputs.json

Where ``inputs.json`` contains a JSON object with keys matching the
card's expected inputs.  The script will print the resulting dossier
to standard output in JSON format.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.cards import CARDS
from mcp.workflow import run_card


async def _run(card_name: str, inputs: Dict[str, Any]) -> None:
    if card_name not in CARDS:
        raise ValueError(f"Unknown card '{card_name}'. Available: {', '.join(CARDS)}")
    card = CARDS[card_name]
    result = await run_card(card, inputs)
    # Output only the dossier for brevity
    print(json.dumps(result.get("dossier", {}), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute an MCP Card workflow")
    parser.add_argument(
        "--card",
        required=True,
        help="Name of the card to execute (e.g. QBR, IncidentPostmortem)",
    )
    parser.add_argument(
        "--inputs",
        required=True,
        type=Path,
        help="Path to a JSON file containing the card input parameters",
    )
    args = parser.parse_args()
    try:
        with args.inputs.open("r", encoding="utf-8") as f:
            inputs = json.load(f)
    except Exception as exc:
        print(f"Failed to read inputs file: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        asyncio.run(_run(args.card, inputs))
    except Exception as exc:
        print(f"Error executing card: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
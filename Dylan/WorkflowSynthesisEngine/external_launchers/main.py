#!/usr/bin/env python3
"""
Script Launcher Pro - Main Entry Point

A production-ready Python script launcher with GUI, CLI, and API interfaces.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cli import cli

if __name__ == '__main__':
    cli()


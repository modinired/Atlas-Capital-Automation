"""
CLI Agent MCP
-------------

This module exposes simple wrappers around local command‑line and
filesystem operations so they can be invoked as MCP tools.  The aim
is to provide a thin layer over the host environment that allows
automated workflows to execute shell commands, edit files and run
tests in a controlled manner.  Because these functions execute
arbitrary code, they should only be enabled for trusted users and
should enforce appropriate sandboxing in production deployments.

The public functions provided here are:

* ``exec`` – run a shell command with optional arguments and a
  timeout.  Returns the captured stdout, stderr and exit code.
* ``edit_repo`` – perform a series of file operations (create,
  modify or delete) against a repository root.  Returns a summary
  of changes made.
* ``test`` – run a pytest suite located at a given path and return
  the results.  This uses the same Python interpreter as the
  application and captures the output for inspection.

In a production system you might expose a more restrictive API,
integrate with a continuous integration service or containerise
execution to prevent host compromise.  The goal here is to
demonstrate how local agents can be exposed as MCP tools.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    returncode: int


async def exec(
    *, cmd: str, args: Optional[List[str]] = None, timeout: int = 30
) -> Dict[str, Any]:
    """Execute a shell command and return its output.

    Parameters
    ----------
    cmd : str
        The command to execute.  This can be an absolute path or a
        program name resolvable via ``PATH``.
    args : list of str, optional
        Arguments to pass to the command.  If provided they will be
        appended to the command in the subprocess call.  Defaults to
        ``None``.
    timeout : int, optional
        Timeout in seconds after which the process will be killed.

    Returns
    -------
    dict
        Contains ``stdout``, ``stderr`` and ``returncode`` keys with
        the corresponding values from the completed process.
    """
    if args is None:
        args = []
    # Build the full command list
    cmd_list: List[str] = [cmd] + args
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "stdout": "",
                "stderr": f"Process timed out after {timeout} seconds",
                "returncode": -1,
            }
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "returncode": proc.returncode,
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": f"Command not found: {cmd}",
            "returncode": -1,
        }


async def edit_repo(
    *, repo: str, ops: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    """Apply a sequence of file operations to a repository.

    Each operation dict must contain an ``action`` key with one of
    ``"create"``, ``"modify"`` or ``"delete"``.  For ``create`` and
    ``modify`` operations a ``path`` and ``content`` must be supplied.
    For ``delete`` operations only the ``path`` is required.  Paths
    are interpreted as relative to the provided ``repo`` root.

    Parameters
    ----------
    repo : str
        Filesystem path to the root of the repository.
    ops : iterable of dict
        Sequence of operations to perform.

    Returns
    -------
    dict
        A summary of the operations applied.  Keys include
        ``changed`` (list of modified file paths) and ``status``
        (string indicating success or error message).
    """
    root = Path(repo).resolve()
    changed: List[str] = []
    for op in ops:
        action = op.get("action")
        rel_path = op.get("path")
        if not isinstance(rel_path, str):
            return {"changed": changed, "status": "Invalid operation: missing 'path'"}
        file_path = (root / rel_path).resolve()
        # Ensure the file stays within the repository root
        if not str(file_path).startswith(str(root)):
            return {"changed": changed, "status": f"Path escapes repository: {rel_path}"}
        if action == "create":
            content = op.get("content", "")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(str(content), encoding="utf-8")
            changed.append(str(file_path))
        elif action == "modify":
            if not file_path.exists():
                return {"changed": changed, "status": f"File does not exist for modify: {rel_path}"}
            content = op.get("content", "")
            file_path.write_text(str(content), encoding="utf-8")
            changed.append(str(file_path))
        elif action == "delete":
            if file_path.is_file():
                file_path.unlink()
                changed.append(str(file_path))
            elif file_path.is_dir():
                # Recursively delete directory
                for child in file_path.rglob('*'):
                    if child.is_file():
                        child.unlink()
                file_path.rmdir()
                changed.append(str(file_path))
            else:
                return {"changed": changed, "status": f"Path does not exist: {rel_path}"}
        else:
            return {"changed": changed, "status": f"Unknown action: {action}"}
    return {"changed": changed, "status": "ok"}


async def test(*, suite: str) -> Dict[str, Any]:
    """Run pytest on a given suite and return the results.

    Parameters
    ----------
    suite : str
        Path to the directory or file containing pytest tests.

    Returns
    -------
    dict
        Contains ``returncode`` and ``output`` from the pytest run.
    """
    # Build the command: use sys.executable to ensure same Python
    cmd = [sys.executable, "-m", "pytest", "-q", suite]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        return {
            "returncode": proc.returncode,
            "output": stdout.decode("utf-8", errors="replace"),
        }
    except Exception as exc:
        return {
            "returncode": -1,
            "output": f"Failed to run pytest: {exc}",
        }
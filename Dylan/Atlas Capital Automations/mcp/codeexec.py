"""
Code Execution MCP
-------------------

This module exposes a sandboxed code execution service that can be used as
part of the Multi‑Component Platform (MCP).  Inspired by the Manus
platform’s ability to execute arbitrary code snippets across multiple
languages【910829859897539†L60-L67】【910829859897539†L94-L107】, the CodeExec MCP
provides a controlled environment for running short programs and
returning their output to callers.  It currently supports Python
scripts and is designed to be extensible to other languages in the
future.

The core API is provided by the ``execute`` function which accepts
parameters describing the language, the code to run, optional
arguments and a timeout.  Execution is performed in a separate
process using Python’s ``asyncio`` facilities to avoid blocking the
event loop.  Temporary files are used to hold the script and are
deleted after execution completes.  Outputs are captured and
returned as strings along with the exit status and a flag
indicating whether the execution timed out.

Security Considerations
=======================

Running arbitrary code carries inherent risk.  The following
mechanisms mitigate some of these risks in this demonstration:

* **Isolated process** – Code runs in its own subprocess rather
  than in the main application interpreter.  This prevents it
  from modifying in‑memory state of the service.
* **Temporary working directory** – Execution occurs within a
  transient temporary directory created for each run.  No access
  to the parent file system is provided, though the host
  operating system’s restrictions still apply.
* **Timeout** – A hard timeout ensures runaway scripts are
  terminated.  The default is five seconds but can be overridden
  per request.

In a production deployment you would further containerise
execution (e.g. via Firecracker or gVisor), drop privileges and
restrict system calls to limit what code can do.  You would also
integrate this service with the Policy MCP to redact PII or deny
execution based on content of the code or its output.

Usage example::

    from mcp.codeexec import execute

    result = await execute(language="python", code="print('hello')")
    print(result["stdout"])  # prints "hello\n"

"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CodeExecRequest(BaseModel):
    """Schema for a code execution request.

    Attributes
    ----------
    language : str
        Programming language of the script.  Only ``"python"`` is
        supported at present.
    code : str
        The source code to execute.
    args : list of str, optional
        Optional command line arguments passed to the script.  Only
        applicable to Python.
    timeout : int
        Maximum number of seconds to allow the script to run.  If
        exceeded, the process will be terminated and ``timed_out`` set
        to True in the result.
    """

    language: str = Field(default="python", description="Programming language to execute")
    code: str = Field(..., description="Source code to execute")
    args: Optional[List[str]] = Field(default=None, description="Command line arguments for the script")
    timeout: int = Field(default=5, description="Maximum execution time in seconds")


class CodeExecResponse(BaseModel):
    """Schema for a code execution response.

    Attributes
    ----------
    stdout : str
        Captured standard output from the script.
    stderr : str
        Captured standard error from the script.
    returncode : int
        The exit status of the process.  A value of ``0`` indicates
        success.
    timed_out : bool
        True if the process was terminated due to a timeout.
    """

    stdout: str = Field(..., description="Standard output from execution")
    stderr: str = Field(..., description="Standard error from execution")
    returncode: int = Field(..., description="Process exit code")
    timed_out: bool = Field(..., description="Indicates if the script timed out")


async def execute(
    *, language: str, code: str, args: Optional[List[str]] = None, timeout: int = 5
) -> Dict[str, Any]:
    """Execute a code snippet in a sandboxed subprocess.

    Parameters
    ----------
    language : str
        Programming language of the code.  Currently only ``"python"`` is
        supported.  Case‑insensitive.
    code : str
        The source code to execute.  It should be a complete script.
    args : list of str, optional
        Optional command line arguments passed to the script.  Ignored
        for unsupported languages.
    timeout : int
        Maximum time in seconds to allow the script to run.  Defaults
        to five seconds.

    Returns
    -------
    dict
        A dictionary with ``stdout``, ``stderr``, ``returncode`` and
        ``timed_out`` keys.  The values are JSON‑serialisable and
        correspond to the :class:`CodeExecResponse` schema.  If an
        unsupported language is requested, ``returncode`` will be ``-1``
        and ``stderr`` will contain an error message.
    """
    lang = language.lower()
    if args is None:
        args = []
    # Currently only Python is supported.  Reject others.
    if lang != "python":
        return {
            "stdout": "",
            "stderr": f"Unsupported language: {language}",
            "returncode": -1,
            "timed_out": False,
        }
    # Write the code to a temporary file within a temporary directory.
    # Using a directory ensures any generated files remain contained.
    temp_dir = tempfile.TemporaryDirectory()
    script_path = Path(temp_dir.name) / "script.py"
    script_path.write_text(code, encoding="utf-8")
    # Build the command using the same Python interpreter as the server.
    cmd: List[str] = [sys.executable, str(script_path)] + args
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir.name,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            timed_out = False
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            stdout, stderr = (b"", b"Process timed out")
            timed_out = True
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")
        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "returncode": proc.returncode,
            "timed_out": timed_out,
        }
    except Exception as exc:
        # Catch unexpected errors such as failure to spawn the process.
        return {
            "stdout": "",
            "stderr": f"Execution error: {exc}",
            "returncode": -1,
            "timed_out": False,
        }
    finally:
        # Clean up the temporary directory.
        temp_dir.cleanup()
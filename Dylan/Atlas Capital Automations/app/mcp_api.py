"""
FastAPI server exposing MCP endpoints.

This module defines a standalone FastAPI application that wraps the
Knowledge, Triangulator and Policy MCPs as HTTP endpoints.  It
provides a convenient way to orchestrate Cards without requiring
direct Python integration.  The routes are nested under ``/mcp``.

To run this server locally:

.. code-block:: bash

    uvicorn app.mcp_api:mcp_app --host 0.0.0.0 --port 9000 --reload

You can then POST to ``/mcp/cards/{card_name}`` with a JSON body
containing the card inputs.  See ``mcp.cards.CARDS`` for
available cards.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List

from mcp.cards import CARDS
from mcp.workflow import run_card
from mcp.knowledge import ground as knowledge_ground, writeback as knowledge_writeback
from mcp.triangulator import route as triangulate_route, adjudicate as triangulate_adjudicate, self_check as triangulate_self_check
from mcp.policy import enforce as policy_enforce, redact as policy_redact
from mcp.codeexec import execute as codeexec_execute


mcp_app = FastAPI(title="MCP Server", version="0.1.0")

# -----------------------------------------------------------------------------
# CORS configuration
#
# The MCP API may be consumed by the new dashboard running on a separate
# port (e.g. Vite dev server).  Permit requests from localhost on common
# development ports.  In production, restrict the origins to your front‑end
# domains.
# -----------------------------------------------------------------------------
mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@mcp_app.post("/mcp/cards/{card_name}")
async def run_card_endpoint(card_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a Card by name with the provided inputs.

    The request body should be a JSON object containing all input
    parameters specified in the card's descriptor.  The response
    includes the execution context and the assembled dossier.
    """
    card = CARDS.get(card_name)
    if not card:
        raise HTTPException(status_code=404, detail=f"Unknown card '{card_name}'")
    result = await run_card(card, inputs)
    return result


@mcp_app.get("/mcp/knowledge/{space}")
async def knowledge_ground_endpoint(space: str, q: str, k: int = 5) -> Dict[str, Any]:
    """Retrieve grounded evidence for a query in a space.

    Query parameters:

    * ``q`` – the search query
    * ``k`` – maximum number of results (default: 5)
    """
    result = knowledge_ground(query=q, space=space, k=k)
    return result


@mcp_app.post("/mcp/knowledge/writeback")
async def knowledge_writeback_endpoint(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Persist a list of documents into the knowledge store.

    Each document should contain ``space`` and ``content`` keys.  The
    function returns a summary with the number of documents written.
    """
    knowledge_writeback(docs)
    return {"written": len(docs)}


@mcp_app.post("/mcp/triangulate/route")
async def triangulate_route_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a task to a list of models and return candidate outputs."""
    task = request.get("task")
    models = request.get("models", [])
    latency_budget_ms = int(request.get("latency_budget_ms", 5000))
    cost_ceiling = float(request.get("cost_ceiling", 1.0))
    candidates = await triangulate_route(task=task, models=models, latency_budget_ms=latency_budget_ms, cost_ceiling=cost_ceiling)
    return {"candidates": candidates}


@mcp_app.post("/mcp/triangulate/adjudicate")
async def triangulate_adjudicate_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Adjudicate a set of candidates based on a rubric."""
    candidates = request.get("candidates")
    rubric = request.get("rubric", [])
    result = triangulate_adjudicate(candidates=candidates, rubric=rubric)
    return result


@mcp_app.post("/mcp/triangulate/self_check")
async def triangulate_self_check_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a self‑check on an output string."""
    output = request.get("output", "")
    checks = request.get("checks", [])
    score = triangulate_self_check(output=output, checks=checks)
    return {"score": score}


@mcp_app.post("/mcp/policy/enforce")
async def policy_enforce_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a policy to a payload."""
    payload = request.get("payload")
    policy_id = request.get("policy_id", "no_pii")
    result = policy_enforce(payload, policy_id)
    return result


@mcp_app.post("/mcp/policy/redact")
async def policy_redact_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive information in a payload."""
    payload = request.get("payload")
    result = policy_redact(payload)
    return result


@mcp_app.post("/mcp/codeexec/execute")
async def codeexec_execute_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a code snippet via the CodeExec MCP.

    The request body should contain at least a ``code`` field with the
    source code to execute.  Optional fields include:

    * ``language`` – programming language (default: ``"python"``)
    * ``args`` – list of command line arguments
    * ``timeout`` – maximum execution time in seconds

    Example::

        {
            "language": "python",
            "code": "print('hello')",
            "args": [],
            "timeout": 5
        }

    Returns the execution result with stdout, stderr, returncode and
    timed_out flags.
    """
    language = request.get("language", "python")
    code = request.get("code")
    if not isinstance(code, str) or not code.strip():
        raise HTTPException(status_code=400, detail="'code' must be a non‑empty string")
    args = request.get("args")
    if args is not None and not isinstance(args, list):
        raise HTTPException(status_code=400, detail="'args' must be a list of strings")
    timeout_val = request.get("timeout", 5)
    try:
        timeout_int = int(timeout_val)
    except Exception:
        raise HTTPException(status_code=400, detail="'timeout' must be an integer")
    result = await codeexec_execute(language=language, code=code, args=args, timeout=timeout_int)
    return result
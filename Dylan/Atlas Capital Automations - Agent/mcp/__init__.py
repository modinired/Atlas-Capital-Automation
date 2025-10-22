"""
Multi‑Component Platform (MCP) package.

This package contains a minimal set of MCP services inspired by the
CESAR‑SRC Symbiotic Recursive Cognition (SRC) architecture.  Each module
represents a logical microservice that can be invoked via simple
function calls or exposed over an HTTP/JSON API.  The goal of this
package is to demonstrate how the existing risk scoring service can be
extended into a more general, multi‑model cognitive platform without
fundamentally changing the underlying logic.

The included MCP servers are:

* ``knowledge`` – persistent evidence store with grounded retrieval and
  write‑back.  Uses an embedded SQLite database for simplicity.
* ``triangulator`` – orchestrates calls across a pool of local
  inference functions, performs A/B/N routing, adjudication and basic
  self‑checking.
* ``policy`` – enforces redaction rules and allowlists on arbitrary
  payloads.  Implements simple PII detection and masking.
* ``workflow`` – compiles and executes task DAGs based on Card
  descriptors.  Coordinates calls to other MCP services.
* ``telemetry`` – exposes helper functions for emitting metrics and
  traces.  It builds on top of the existing Prometheus/OpenTelemetry
  instrumentation defined in the ``app`` package.
* ``cards`` – predefined Card templates implementing common
  orchestration patterns (e.g. Quarterly Business Review, Incident
  Postmortem).  Cards encapsulate plan definitions, evidence
  contracts, rubrics and outputs.

These components are intentionally lightweight and synchronous for
clarity.  In a production environment they should be exposed via
FastAPI or another RPC layer and executed asynchronously.  The
``cards`` module demonstrates how the SRC loop can be assembled using
these primitives.

Usage example::

    from mcp.cards import CARDS
    from mcp.workflow import run_card

    card = CARDS["QBR"]
    inputs = {"accounts": ["ACME"], "time_window": "90d"}
    result = run_card(card, inputs)
    print(result["dossier"])  # access the decision dossier

All functions return plain Python data structures (dicts, lists,
Pydantic models) so they can be easily serialized to JSON.
"""

from . import knowledge  # noqa: F401
from . import triangulator  # noqa: F401
from . import policy  # noqa: F401
from . import workflow  # noqa: F401
from . import telemetry  # noqa: F401
from . import cards  # noqa: F401
from . import cli_agent  # noqa: F401
from . import codeexec  # noqa: F401